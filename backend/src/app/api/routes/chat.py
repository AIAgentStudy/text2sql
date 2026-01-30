"""
채팅 API 엔드포인트

자연어 질문을 SQL로 변환하고 결과를 반환하는 SSE 스트리밍 API입니다.
"""

import json
import logging
from typing import AsyncGenerator

from fastapi import APIRouter, HTTPException
from sse_starlette.sse import EventSourceResponse

from app.agent.graph import get_graph
from app.agent.state import create_initial_state
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
)
from app.session.manager import (
    add_message_to_session,
    get_checkpointer,
    get_or_create_session,
    update_session_activity,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/chat",
    summary="새로운 질문 전송",
    description="자연어 질문을 전송하고 SQL 쿼리 생성을 시작합니다. SSE를 통해 진행 상황을 스트리밍합니다.",
)
async def chat_endpoint(request: ChatRequest) -> EventSourceResponse:
    """
    채팅 엔드포인트 - SSE 스트리밍

    자연어 질문을 받아 SQL 쿼리를 생성하고 실행 결과를 스트리밍합니다.
    """

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

            # 초기 상태 생성
            initial_state = create_initial_state(
                user_question=request.message,
                session_id=session_id,
            )

            # 그래프 실행 및 스트리밍
            final_state = None
            async for event in graph.astream(initial_state, config):
                # 노드별 이벤트 처리
                for node_name, node_output in event.items():
                    final_state = node_output

                    # 쿼리 생성 완료 시
                    if node_name == "query_generation" and node_output.get("generated_query"):
                        yield _format_sse_event(
                            StatusEvent(
                                status=QueryRequestStatus.EXECUTING,
                                message="쿼리를 실행하고 있습니다...",
                            )
                        )
                        yield _format_sse_event(
                            QueryPreviewEvent(
                                query=node_output.get("generated_query", ""),
                                explanation=node_output.get("query_explanation", ""),
                            )
                        )

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
async def confirm_query(request: ConfirmationRequest) -> ConfirmationResponse:
    """
    쿼리 실행 확인 엔드포인트

    Human-in-the-Loop: 사용자가 쿼리 실행을 승인하면 실행합니다.
    (현재 버전에서는 자동 실행, 추후 US3에서 구현)
    """
    try:
        if not request.approved:
            return ConfirmationResponse(
                success=True,
                result=None,
                error=None,
            )

        # 승인 시 처리 (US3에서 구현)
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
