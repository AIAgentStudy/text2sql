"""
LangGraph 워크플로우 정의

Text2SQL 에이전트의 전체 워크플로우를 구성합니다.
"""

import logging
from typing import Literal

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from app.agent.nodes.query_execution import query_execution_node
from app.agent.nodes.query_generation import query_generation_node
from app.agent.nodes.query_validation import (
    query_validation_node,
    MAX_VALIDATION_RETRIES,
)
from app.agent.nodes.response_formatting import response_formatting_node
from app.agent.nodes.schema_retrieval import schema_retrieval_node
from app.agent.nodes.user_confirmation import user_confirmation_node
from app.agent.state import Text2SQLAgentState

logger = logging.getLogger(__name__)


def should_continue_after_schema(
    state: Text2SQLAgentState,
) -> Literal["generate", "format_error"]:
    """
    스키마 조회 후 다음 단계 결정

    스키마 조회 중 에러(권한 부족 등)가 발생하면 즉시 응답 포맷팅으로 이동
    """
    if state.get("execution_error"):
        return "format_error"
    return "generate"


def should_continue_after_generation(
    state: Text2SQLAgentState,
) -> Literal["validate", "format_error"]:
    """
    쿼리 생성 후 다음 단계 결정

    쿼리가 성공적으로 생성되었으면 검증, 아니면 에러 포맷팅으로 이동
    """
    if state.get("execution_error") or not state.get("generated_query"):
        return "format_error"
    return "validate"


def should_continue_after_validation(
    state: Text2SQLAgentState,
) -> Literal["confirm", "regenerate", "format_error"]:
    """
    쿼리 검증 후 다음 단계 결정

    - 유효하면 사용자 확인 단계로
    - 재시도 가능하면 재생성
    - 최대 재시도 초과 시 에러 포맷팅
    """
    is_valid = state.get("is_query_valid", False)
    attempt = state.get("generation_attempt", 0)

    if is_valid:
        return "confirm"

    # 재시도 가능 여부 확인
    if attempt < MAX_VALIDATION_RETRIES:
        logger.info(f"쿼리 재생성 시도 ({attempt}/{MAX_VALIDATION_RETRIES})")
        return "regenerate"

    # 최대 재시도 초과
    logger.warning(f"최대 재시도 횟수({MAX_VALIDATION_RETRIES}) 도달, 실패 처리")
    return "format_error"


def should_continue_after_confirmation(
    state: Text2SQLAgentState,
) -> Literal["execute", "revalidate", "format_cancelled"]:
    """
    사용자 확인 후 다음 단계 결정

    - 승인되면 실행
    - 수정된 쿼리가 있으면 재검증
    - 거부되면 취소 포맷팅
    """
    user_approved = state.get("user_approved")

    if user_approved is True:
        # 수정된 쿼리가 있고 재검증이 필요한 경우
        if state.get("is_query_valid") is False:
            return "revalidate"
        return "execute"

    # 거부되거나 아직 응답이 없는 경우
    return "format_cancelled"


def should_continue_after_execution(
    state: Text2SQLAgentState,
) -> Literal["format_result"]:
    """
    쿼리 실행 후 다음 단계 결정

    실행 결과(성공/실패)를 포맷팅 노드로 전달
    """
    return "format_result"


def build_graph() -> StateGraph:
    """
    Text2SQL 에이전트 그래프 빌드

    워크플로우:
    START → 스키마 조회 → (권한 체크) → 쿼리 생성 → 쿼리 검증 → 사용자 확인 → 쿼리 실행 → 응답 포맷팅 → END
                  ↓ (권한 없음)          ↑           ↓ (재시도)     ↓ (수정됨)
            응답 포맷팅                  └───────────┘            쿼리 검증
                                                    ↓ (실패)        ↓ (취소)
                                              응답 포맷팅 ←─────────┘

    Returns:
        StateGraph: 컴파일되지 않은 그래프
    """
    logger.info("Text2SQL 에이전트 그래프 빌드 시작")

    # 그래프 생성
    graph = StateGraph(Text2SQLAgentState)

    # 노드 추가
    graph.add_node("schema_retrieval", schema_retrieval_node)
    graph.add_node("query_generation", query_generation_node)
    graph.add_node("query_validation", query_validation_node)
    graph.add_node("user_confirmation", user_confirmation_node)
    graph.add_node("query_execution", query_execution_node)
    graph.add_node("response_formatting", response_formatting_node)

    # 엣지 추가
    # START → 스키마 조회
    graph.add_edge(START, "schema_retrieval")

    # 스키마 조회 → 조건부 분기 (쿼리 생성 또는 에러)
    graph.add_conditional_edges(
        "schema_retrieval",
        should_continue_after_schema,
        {
            "generate": "query_generation",
            "format_error": "response_formatting",
        },
    )

    # 쿼리 생성 → 조건부 분기 (검증 또는 에러)
    graph.add_conditional_edges(
        "query_generation",
        should_continue_after_generation,
        {
            "validate": "query_validation",
            "format_error": "response_formatting",
        },
    )

    # 쿼리 검증 → 조건부 분기 (확인, 재생성, 또는 에러)
    graph.add_conditional_edges(
        "query_validation",
        should_continue_after_validation,
        {
            "confirm": "user_confirmation",
            "regenerate": "query_generation",
            "format_error": "response_formatting",
        },
    )

    # 사용자 확인 → 조건부 분기 (실행, 재검증, 또는 취소)
    graph.add_conditional_edges(
        "user_confirmation",
        should_continue_after_confirmation,
        {
            "execute": "query_execution",
            "revalidate": "query_validation",
            "format_cancelled": "response_formatting",
        },
    )

    # 쿼리 실행 → 응답 포맷팅
    graph.add_conditional_edges(
        "query_execution",
        should_continue_after_execution,
        {
            "format_result": "response_formatting",
        },
    )

    # 응답 포맷팅 → END
    graph.add_edge("response_formatting", END)

    logger.info("Text2SQL 에이전트 그래프 빌드 완료")
    return graph


def compile_graph(checkpointer: MemorySaver | None = None) -> StateGraph:
    """
    Text2SQL 에이전트 그래프 컴파일

    Args:
        checkpointer: 상태 체크포인터 (세션 지속성용)

    Returns:
        컴파일된 그래프
    """
    graph = build_graph()

    # user_confirmation_node 내부에서 interrupt()를 직접 호출하므로
    # interrupt_before는 사용하지 않음 (이중 interrupt 방지)
    if checkpointer:
        compiled = graph.compile(checkpointer=checkpointer)
    else:
        compiled = graph.compile()

    logger.info("Text2SQL 에이전트 그래프 컴파일 완료")
    return compiled


# 기본 체크포인터로 컴파일된 그래프 (개발용)
_default_checkpointer = MemorySaver()
default_graph = compile_graph(_default_checkpointer)


def get_graph(checkpointer: MemorySaver | None = None) -> StateGraph:
    """
    그래프 인스턴스 반환

    Args:
        checkpointer: 커스텀 체크포인터 (None이면 기본값 사용)

    Returns:
        컴파일된 그래프
    """
    if checkpointer:
        return compile_graph(checkpointer)
    return default_graph
