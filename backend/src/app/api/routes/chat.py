"""
채팅 API 엔드포인트

자연어 질문을 SQL로 변환하고 결과를 반환하는 SSE 스트리밍 API입니다.
"""

import json
import logging
from typing import Annotated, AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException
from langgraph.types import Command
from sse_starlette.sse import EventSourceResponse

from app.agent.graph import get_graph
from app.agent.state import create_initial_state
from app.auth.dependencies import get_current_user
from app.auth.permissions import get_accessible_tables
from app.models.auth import UserWithRoles
from app.models.entities import QueryRequestStatus
from app.models.requests import ChatRequest, ConfirmationRequest
from app.models.responses import (
    ConfirmationResponse,
    DoneEvent,
    ErrorDetail,
    ErrorEvent,
    QueryPreviewEvent,
    QueryResultData,
    ResultEvent,
    SessionEvent,
    StatusEvent,
    ConfirmationRequiredEvent,
)
from app.session.manager import (
    add_message_to_session,
    get_checkpointer,
    get_or_create_session,
    get_session,
    update_session_activity,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/chat",
    summary="새로운 질문 전송",
    description="자연어 질문을 전송하고 SQL 쿼리 생성을 시작합니다. SSE를 통해 진행 상황을 스트리밍합니다.",
)
async def chat_endpoint(
    request: ChatRequest,
    current_user: Annotated[UserWithRoles, Depends(get_current_user)],
) -> EventSourceResponse:
    """
    채팅 엔드포인트 - SSE 스트리밍

    자연어 질문을 받아 SQL 쿼리를 생성하고 실행 결과를 스트리밍합니다.
    인증된 사용자만 접근 가능하며, 사용자 역할에 따라 접근 가능한 테이블이 제한됩니다.
    """
    # 사용자가 접근 가능한 테이블 목록 조회
    accessible_tables = await get_accessible_tables(current_user, "read")

    async def event_generator() -> AsyncGenerator[dict[str, str], None]:
        try:
            # 세션 조회/생성
            session = get_or_create_session(
                request.session_id,
                request.llm_provider,
            )
            session_id = session.session_id

            # 세션 이벤트 전송
            yield _format_sse_event(
                SessionEvent(session_id=session_id)
            )

            # 상태 이벤트: 생성 중
            yield _format_sse_event(
                StatusEvent(
                    status=QueryRequestStatus.GENERATING,
                    message="쿼리를 생성하고 있습니다...",
                )
            )

            # 사용자 메시지 저장
            add_message_to_session(session_id, "user", request.message)

            # 에이전트 그래프 실행
            graph = get_graph(get_checkpointer())
            config = {"configurable": {"thread_id": session_id}}

            # 초기 상태 생성 (사용자 권한 정보 포함)
            initial_state = create_initial_state(
                user_question=request.message,
                session_id=session_id,
                accessible_tables=accessible_tables,
                user_id=current_user.id,
                user_roles=current_user.roles,
                llm_provider=request.llm_provider,
            )

            # 그래프 실행 및 스트리밍
            final_state = None
            is_interrupted = False
            current_query_id = ""  # query_id 추적용

            async for event in graph.astream(
                initial_state, config, stream_mode="updates"
            ):
                # 노드별 이벤트 처리
                for node_name, node_output in event.items():
                    # __interrupt__ 이벤트 처리 (Human-in-the-Loop)
                    if node_name == "__interrupt__":
                        is_interrupted = True
                        # interrupt 값에서 확인 요청 정보 추출
                        if isinstance(node_output, tuple) and len(node_output) > 0:
                            interrupt_value = getattr(
                                node_output[0], "value", None
                            )
                            if isinstance(interrupt_value, dict):
                                yield _format_sse_event(
                                    ConfirmationRequiredEvent(
                                        query_id=interrupt_value.get(
                                            "query_id", current_query_id
                                        ),
                                        query=interrupt_value.get("query", ""),
                                        explanation=interrupt_value.get(
                                            "explanation", ""
                                        ),
                                    )
                                )
                        continue

                    # dict가 아닌 이벤트 건너뛰기
                    if not isinstance(node_output, dict):
                        continue

                    final_state = node_output

                    # query_id 추적 (어느 노드에서든 설정되면 저장)
                    if node_output.get("query_id"):
                        current_query_id = node_output.get("query_id")

                    # 쿼리 생성 완료 시
                    if node_name == "query_generation" and node_output.get(
                        "generated_query"
                    ):
                        yield _format_sse_event(
                            StatusEvent(
                                status=QueryRequestStatus.VALIDATING,
                                message="쿼리를 검증하고 있습니다...",
                            )
                        )
                        yield _format_sse_event(
                            QueryPreviewEvent(
                                query=node_output.get("generated_query", ""),
                                explanation=node_output.get(
                                    "query_explanation", ""
                                ),
                            )
                        )

                    # 검증 완료 시
                    if node_name == "query_validation" and node_output.get(
                        "is_query_valid"
                    ):
                        yield _format_sse_event(
                            StatusEvent(
                                status=QueryRequestStatus.AWAITING_CONFIRM,
                                message="쿼리 확인을 기다리고 있습니다...",
                            )
                        )

                    # 쿼리 실행 중
                    if node_name == "query_execution":
                        yield _format_sse_event(
                            StatusEvent(
                                status=QueryRequestStatus.EXECUTING,
                                message="쿼리를 실행하고 있습니다...",
                            )
                        )

            # 인터럽트 상태인 경우 (Human-in-the-Loop)
            if is_interrupted:
                yield _format_sse_event(DoneEvent(awaiting_confirmation=True))
                update_session_activity(session_id)
                return

            # 최종 결과 전송
            if final_state:
                if final_state.get("execution_error"):
                    yield _format_sse_event(
                        ErrorEvent(
                            error=ErrorDetail(
                                code="EXECUTION_ERROR",
                                message=final_state.get("execution_error", ""),
                            )
                        )
                    )
                else:
                    # 결과 이벤트
                    rows = final_state.get("query_result", [])
                    columns = final_state.get("result_columns", [])

                    yield _format_sse_event(
                        ResultEvent(
                            data=QueryResultData(
                                rows=rows,
                                total_row_count=final_state.get("total_row_count", 0),
                                returned_row_count=len(rows),
                                columns=[],  # 단순화
                                is_truncated=len(rows) < final_state.get("total_row_count", 0),
                                execution_time_ms=final_state.get("execution_time_ms", 0),
                            )
                        )
                    )

                    # 어시스턴트 응답 저장
                    add_message_to_session(
                        session_id,
                        "assistant",
                        final_state.get("final_response", ""),
                    )

            # 완료 이벤트
            yield _format_sse_event(DoneEvent())

            # 세션 활동 시간 업데이트
            update_session_activity(session_id)

        except Exception as e:
            logger.exception(f"채팅 처리 중 오류: {e}")
            yield _format_sse_event(
                ErrorEvent(
                    error=ErrorDetail(
                        code="INTERNAL_ERROR",
                        message="요청을 처리하는 중 오류가 발생했습니다.",
                    )
                )
            )
            yield _format_sse_event(DoneEvent())

    return EventSourceResponse(event_generator())


@router.post(
    "/chat/confirm",
    response_model=ConfirmationResponse,
    summary="쿼리 실행 확인",
    description="생성된 쿼리의 실행을 승인하거나 취소합니다.",
)
async def confirm_query(
    request: ConfirmationRequest,
    current_user: Annotated[UserWithRoles, Depends(get_current_user)],
) -> ConfirmationResponse:
    """
    쿼리 실행 확인 엔드포인트

    Human-in-the-Loop: 사용자가 쿼리 실행을 승인하면 실행합니다.
    LangGraph Command(resume)를 사용하여 일시 중지된 워크플로우를 재개합니다.
    인증된 사용자만 접근 가능합니다.
    """
    try:
        session_id = request.session_id
        query_id = request.query_id

        logger.info(
            f"쿼리 확인 요청 - 세션: {session_id}, 쿼리: {query_id}, 승인: {request.approved}"
        )

        # 세션 확인
        session = get_session(session_id)
        if not session:
            logger.warning(f"세션을 찾을 수 없음: {session_id}")
            return ConfirmationResponse(
                success=False,
                result=None,
                error=ErrorDetail(
                    code="SESSION_NOT_FOUND",
                    message="세션이 만료되었거나 존재하지 않습니다.",
                ),
            )

        # 그래프 가져오기
        graph = get_graph(get_checkpointer())
        config = {"configurable": {"thread_id": session_id}}

        # 사용자 응답 구성
        user_response = {
            "approved": request.approved,
            "modified_query": request.modified_query,
        }

        if not request.approved:
            # 거부 시 Command(resume)로 재개하되 거부 상태 전달
            logger.info(f"사용자가 쿼리 실행을 거부함: {query_id}")

            # Command로 워크플로우 재개 (거부 상태)
            final_state = {}
            async for event in graph.astream(
                Command(resume=user_response), config, stream_mode="updates"
            ):
                for node_name, node_output in event.items():
                    if not isinstance(node_output, dict):
                        continue
                    final_state.update(node_output)

            return ConfirmationResponse(
                success=True,
                result=None,
                error=None,
            )

        # 승인 시 Command(resume)로 워크플로우 재개
        logger.info(f"사용자가 쿼리 실행을 승인함: {query_id}")

        # 수정된 쿼리가 있는 경우
        if request.modified_query:
            logger.info(f"수정된 쿼리로 실행: {request.modified_query[:50]}...")

        # Command로 워크플로우 재개
        final_state = {}
        async for event in graph.astream(
            Command(resume=user_response), config, stream_mode="updates"
        ):
            for node_name, node_output in event.items():
                if not isinstance(node_output, dict):
                    continue
                final_state.update(node_output)

        # 결과 반환
        if final_state:
            if final_state.get("execution_error"):
                return ConfirmationResponse(
                    success=False,
                    result=None,
                    error=ErrorDetail(
                        code="EXECUTION_ERROR",
                        message=final_state.get("execution_error", ""),
                    ),
                )

            return ConfirmationResponse(
                success=True,
                result=QueryResultData(
                    rows=final_state.get("query_result", []),
                    total_row_count=final_state.get("total_row_count", 0),
                    returned_row_count=len(final_state.get("query_result", [])),
                    columns=[],
                    is_truncated=False,
                    execution_time_ms=final_state.get("execution_time_ms", 0),
                ),
                error=None,
            )

        return ConfirmationResponse(
            success=True,
            result=None,
            error=None,
        )

    except Exception as e:
        logger.exception(f"확인 처리 중 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


def _format_sse_event(event: object) -> dict[str, str]:
    """SSE 이벤트 포맷팅"""
    if hasattr(event, "model_dump"):
        data = event.model_dump()  # type: ignore[union-attr]
    else:
        data = {"type": "unknown"}

    return {
        "event": "message",
        "data": json.dumps(data, ensure_ascii=False, default=str),
    }
