"""
사용자 확인 노드

Human-in-the-Loop: LangGraph의 interrupt()를 사용하여
사용자가 쿼리 실행을 승인하거나 취소할 수 있도록 합니다.
"""

import logging
from typing import Literal

from langgraph.types import interrupt

from app.agent.state import Text2SQLAgentState
from app.config import get_settings

logger = logging.getLogger(__name__)


async def user_confirmation_node(
    state: Text2SQLAgentState,
) -> dict[str, object]:
    """
    사용자 확인 노드

    쿼리 실행 전 사용자에게 승인을 요청합니다.
    interrupt()를 통해 워크플로우를 일시 중지하고
    사용자의 응답을 기다립니다.

    Args:
        state: 현재 에이전트 상태

    Returns:
        업데이트할 상태 딕셔너리
    """
    settings = get_settings()

    # 자동 확인 모드인 경우 바로 승인
    if settings.auto_confirm_queries:
        logger.info("자동 확인 모드: 쿼리 자동 승인")
        return {
            "user_approved": True,
        }

    generated_query = state.get("generated_query", "")
    query_explanation = state.get("query_explanation", "")
    query_id = state.get("query_id", "")

    logger.info(f"사용자 확인 요청 - 쿼리 ID: {query_id}")

    # 확인 요청 정보 구성
    confirmation_request = {
        "type": "query_confirmation",
        "query_id": query_id,
        "query": generated_query,
        "explanation": query_explanation,
        "message": "다음 쿼리를 실행할까요?",
        "options": {
            "approve": "실행",
            "reject": "취소",
            "modify": "수정",
        },
    }

    # interrupt()를 호출하여 워크플로우 일시 중지
    # Command(resume=...)로 재개될 때까지 대기
    user_response = interrupt(confirmation_request)

    logger.info(f"사용자 응답 수신: {user_response}")

    # 사용자 응답 처리
    return handle_user_response(state, user_response)


def handle_user_response(
    state: Text2SQLAgentState,
    response: dict[str, object] | bool,
) -> dict[str, object]:
    """
    사용자 응답 처리

    Args:
        state: 현재 에이전트 상태
        response: 사용자 응답 (dict 또는 bool)

    Returns:
        업데이트할 상태 딕셔너리
    """
    # bool 타입 응답 처리 (단순 승인/거부)
    if isinstance(response, bool):
        approved = response
        modified_query = None
    elif isinstance(response, dict):
        approved = response.get("approved", False)
        modified_query = response.get("modified_query")
    else:
        logger.warning(f"예상치 못한 응답 타입: {type(response)}")
        approved = False
        modified_query = None

    if approved:
        logger.info("사용자가 쿼리 실행을 승인함")
        result: dict[str, object] = {"user_approved": True}

        # 수정된 쿼리가 있으면 업데이트
        if modified_query:
            logger.info(f"수정된 쿼리로 변경: {modified_query[:50]}...")
            result["generated_query"] = modified_query
            # 수정된 쿼리는 재검증 필요
            result["is_query_valid"] = False

        return result
    else:
        logger.info("사용자가 쿼리 실행을 거부함")
        return {
            "user_approved": False,
            "execution_error": "사용자가 쿼리 실행을 취소했습니다.",
        }


def should_wait_for_confirmation(state: Text2SQLAgentState) -> bool:
    """
    사용자 확인이 필요한지 확인

    Args:
        state: 현재 에이전트 상태

    Returns:
        확인 필요 여부
    """
    settings = get_settings()

    # 자동 확인 모드면 대기 불필요
    if settings.auto_confirm_queries:
        return False

    # 이미 승인/거부된 경우
    if state.get("user_approved") is not None:
        return False

    # 쿼리가 유효하지 않으면 확인 불필요
    if not state.get("is_query_valid", False):
        return False

    return True


def get_confirmation_status(
    state: Text2SQLAgentState,
) -> Literal["pending", "approved", "rejected", "not_required"]:
    """
    확인 상태 반환

    Args:
        state: 현재 에이전트 상태

    Returns:
        확인 상태
    """
    settings = get_settings()

    if settings.auto_confirm_queries:
        return "not_required"

    user_approved = state.get("user_approved")

    if user_approved is None:
        return "pending"
    elif user_approved is True:
        return "approved"
    else:
        return "rejected"
