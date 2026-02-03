"""
LangGraph 에이전트 상태 정의

Text2SQL 워크플로우에서 사용하는 상태를 TypedDict로 정의합니다.
"""

from typing import Annotated, Literal, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class Text2SQLAgentState(TypedDict):
    """Text2SQL 에이전트 상태 정의"""

    # === 입력 ===
    user_question: str
    """사용자의 자연어 질문"""

    session_id: str
    """세션 ID"""

    llm_provider: Literal["openai", "anthropic", "google"]
    """사용할 LLM 프로바이더"""

    # === 대화 컨텍스트 ===
    messages: Annotated[list[BaseMessage], add_messages]
    """대화 히스토리 (add_messages 리듀서로 자동 누적)"""

    # === 스키마 컨텍스트 ===
    database_schema: str
    """데이터베이스 스키마 정보 (문자열 형태)"""

    relevant_tables: list[str]
    """관련 테이블 목록"""

    accessible_tables: list[str]
    """사용자 권한에 따라 접근 가능한 테이블 목록"""

    user_id: int | None
    """현재 사용자 ID"""

    user_roles: list[str]
    """현재 사용자 역할 목록"""

    # === 쿼리 생성 ===
    generated_query: str
    """생성된 SQL 쿼리"""

    query_explanation: str
    """쿼리에 대한 한국어 설명"""

    generation_attempt: int
    """현재 쿼리 생성 시도 횟수"""

    # === 검증 ===
    validation_errors: list[str]
    """검증 오류 메시지 목록"""

    is_query_valid: bool
    """쿼리 유효성 여부"""

    # === 사용자 확인 (Human-in-the-Loop) ===
    user_approved: bool | None
    """사용자 승인 여부 (None=대기 중, True=승인, False=거부)"""

    query_id: str
    """현재 쿼리 ID (확인 요청 시 사용)"""

    # === 실행 결과 ===
    query_result: list[dict[str, object]]
    """쿼리 실행 결과 (행 목록)"""

    result_columns: list[str]
    """결과 컬럼 목록"""

    total_row_count: int
    """전체 결과 행 수"""

    execution_time_ms: int
    """쿼리 실행 시간 (밀리초)"""

    execution_error: str | None
    """실행 오류 메시지"""

    # === 최종 응답 ===
    final_response: str
    """최종 응답 메시지"""

    response_format: Literal["table", "summary", "error"]
    """응답 형식"""


def create_initial_state(
    user_question: str,
    session_id: str,
    accessible_tables: list[str] | None = None,
    user_id: int | None = None,
    user_roles: list[str] | None = None,
    llm_provider: Literal["openai", "anthropic", "google"] = "openai",
) -> Text2SQLAgentState:
    """초기 에이전트 상태 생성"""
    return Text2SQLAgentState(
        # 입력
        user_question=user_question,
        session_id=session_id,
        llm_provider=llm_provider,
        # 대화 컨텍스트
        messages=[],
        # 스키마 컨텍스트
        database_schema="",
        relevant_tables=[],
        accessible_tables=accessible_tables or [],
        user_id=user_id,
        user_roles=user_roles or [],
        # 쿼리 생성
        generated_query="",
        query_explanation="",
        generation_attempt=0,
        # 검증
        validation_errors=[],
        is_query_valid=False,
        # 사용자 확인
        user_approved=None,
        query_id="",
        # 실행 결과
        query_result=[],
        result_columns=[],
        total_row_count=0,
        execution_time_ms=0,
        execution_error=None,
        # 최종 응답
        final_response="",
        response_format="table",
    )
