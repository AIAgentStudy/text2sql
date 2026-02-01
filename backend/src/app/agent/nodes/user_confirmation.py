"""
사용자 확인 노드

Human-in-the-Loop: LangGraph interrupt()를 사용하여 사용자 확인을 요청합니다.
"""

import logging
from dataclasses import dataclass

from langgraph.types import interrupt

from app.agent.state import Text2SQLAgentState

logger = logging.getLogger(__name__)


@dataclass
class ConfirmationRequired(Exception):
    """사용자 확인이 필요할 때 발생하는 예외"""

    query_id: str
    query: str
    explanation: str


@dataclass
class QueryConfirmationRequest:
    """쿼리 확인 요청 데이터"""

    query_id: str
    query: str
    explanation: str
    message: str = "이 쿼리를 실행하시겠습니까?"


def user_confirmation_node(state: Text2SQLAgentState) -> dict[str, object]:
    """
    사용자 확인 노드

    생성된 쿼리를 실행하기 전에 사용자 확인을 요청합니다.
    LangGraph의 interrupt() 함수를 사용하여 그래프 실행을 일시 중지합니다.

    Args:
        state: 현재 에이전트 상태

    Returns:
        업데이트할 상태 딕셔너리

    흐름:
    1. user_approved가 None이면 interrupt 발생 (확인 대기)
    2. user_approved가 True이면 실행 계속
    3. user_approved가 False이면 취소 처리
    """
    query_id = state.get("query_id", "")
    generated_query = state.get("generated_query", "")
    query_explanation = state.get("query_explanation", "")
    user_approved = state.get("user_approved")

    logger.info(f"사용자 확인 노드 - query_id: {query_id}, approved: {user_approved}")

    # 이미 승인된 경우
    if user_approved is True:
        logger.info("쿼리 실행 승인됨")
        return {
            "user_approved": True,
        }

    # 거부된 경우
    if user_approved is False:
        logger.info("쿼리 실행 거부됨")
        return {
            "user_approved": False,
            "execution_error": "사용자가 쿼리 실행을 취소했습니다.",
            "response_format": "error",
        }

    # 대기 중인 경우 - interrupt 발생
    logger.info("사용자 확인 대기 중 - interrupt 발생")

    # LangGraph interrupt 호출
    # 이 함수는 그래프 실행을 일시 중지하고 클라이언트에게 확인 요청을 전달합니다
    confirmation_request = QueryConfirmationRequest(
        query_id=query_id,
        query=generated_query,
        explanation=query_explanation,
        message="실행하기 전에 쿼리를 확인해주세요.",
    )

    # interrupt()를 호출하면 그래프 실행이 일시 중지됩니다
    # Command(resume=...)로 재개할 때까지 대기합니다
    interrupt(
        {
            "type": "confirmation_required",
            "query_id": query_id,
            "query": generated_query,
            "explanation": query_explanation,
            "message": confirmation_request.message,
        }
    )

    # interrupt 이후 재개되면 여기로 돌아옵니다
    # 하지만 실제로는 Command(resume=..., update=...)로 상태가 업데이트되므로
    # 이 반환값은 사용되지 않을 수 있습니다
    return {
        "user_approved": None,
    }


def create_confirmation_response(
    query_id: str,
    query: str,
    explanation: str,
) -> dict[str, object]:
    """
    확인 요청 응답 생성

    Args:
        query_id: 쿼리 ID
        query: SQL 쿼리
        explanation: 쿼리 설명

    Returns:
        확인 요청 응답 딕셔너리
    """
    return {
        "type": "confirmation_required",
        "query_id": query_id,
        "query": query,
        "explanation": explanation,
        "message": "이 쿼리를 실행하시겠습니까?",
    }
