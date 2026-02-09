"""
LangGraph 에이전트 상태 정의

Text2SQL 워크플로우에서 사용하는 상태를 Nested TypedDict로 정의합니다.
논리적 그룹화를 통해 노드별 책임을 명확히 하고 디버깅을 용이하게 합니다.
"""

from typing import Annotated, Literal, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


# === Nested Context TypedDicts ===


class InputContext(TypedDict):
    """입력 컨텍스트 - 사용자 질문 및 세션 정보"""

    user_question: str
    """사용자의 자연어 질문"""

    session_id: str
    """세션 ID"""

    llm_provider: Literal["openai", "anthropic", "google"]
    """사용할 LLM 프로바이더"""


class AuthContext(TypedDict):
    """인증 컨텍스트 - 사용자 권한 정보"""

    user_id: int | None
    """현재 사용자 ID"""

    user_roles: list[str]
    """현재 사용자 역할 목록"""

    accessible_tables: list[str]
    """사용자 권한에 따라 접근 가능한 테이블 목록"""


class SchemaContext(TypedDict):
    """스키마 컨텍스트 - 데이터베이스 스키마 정보"""

    database_schema: str
    """데이터베이스 스키마 정보 (문자열 형태)"""

    relevant_tables: list[str]
    """관련 테이블 목록"""


class QueryGeneration(TypedDict):
    """쿼리 생성 - SQL 쿼리 생성 관련 상태"""

    generated_query: str
    """생성된 SQL 쿼리"""

    query_explanation: str
    """쿼리에 대한 한국어 설명"""

    generation_attempt: int
    """현재 쿼리 생성 시도 횟수"""

    query_id: str
    """현재 쿼리 ID (확인 요청 시 사용)"""


class ValidationResult(TypedDict):
    """검증 결과 - 쿼리 유효성 검증 결과"""

    validation_errors: list[str]
    """검증 오류 메시지 목록"""

    is_query_valid: bool
    """쿼리 유효성 여부"""


class ExecutionResult(TypedDict):
    """실행 결과 - 쿼리 실행 결과"""

    query_result: list[dict[str, object]]
    """쿼리 실행 결과 (행 목록)"""

    result_columns: list[dict[str, object]]
    """결과 컬럼 목록 (name, data_type, is_nullable)"""

    total_row_count: int
    """전체 결과 행 수"""

    execution_time_ms: int
    """쿼리 실행 시간 (밀리초)"""

    execution_error: str | None
    """실행 오류 메시지"""


class ResponseOutput(TypedDict):
    """응답 출력 - 최종 응답 정보"""

    user_approved: bool | None
    """사용자 승인 여부 (None=대기 중, True=승인, False=거부)"""

    final_response: str
    """최종 응답 메시지"""

    response_format: Literal["table", "summary", "error"]
    """응답 형식"""


class NodeTiming(TypedDict):
    """노드 타이밍 정보"""

    node_name: str
    """노드 이름"""

    start_time: float
    """시작 시간 (timestamp)"""

    end_time: float | None
    """종료 시간 (timestamp)"""

    duration_ms: float | None
    """소요 시간 (밀리초)"""


class ErrorEntry(TypedDict):
    """에러 체인 항목"""

    node_name: str
    """에러 발생 노드"""

    error_type: str
    """에러 타입"""

    error_message: str
    """에러 메시지"""

    timestamp: float
    """발생 시간 (timestamp)"""

    context: dict[str, object]
    """추가 컨텍스트 정보"""


class RetryRecord(TypedDict):
    """재시도 기록"""

    node_name: str
    """재시도 발생 노드"""

    attempt: int
    """시도 횟수"""

    reason: str
    """재시도 사유"""

    timestamp: float
    """발생 시간 (timestamp)"""


class DebugContext(TypedDict):
    """디버그 컨텍스트 - 실행 추적 및 에러 체인"""

    trace_id: str
    """추적 ID (요청 단위)"""

    node_timings: list[NodeTiming]
    """노드별 실행 시간 기록"""

    error_chain: list[ErrorEntry]
    """에러 체인 (에러 발생 순서대로 기록)"""

    current_node: str
    """현재 실행 중인 노드"""

    retry_history: list[RetryRecord]
    """재시도 히스토리"""


# === Main Agent State ===


class Text2SQLAgentState(TypedDict):
    """Text2SQL 에이전트 상태 정의 (Nested 구조)"""

    # 중첩 컨텍스트
    input: InputContext
    """입력 컨텍스트"""

    auth: AuthContext
    """인증 컨텍스트"""

    schema: SchemaContext
    """스키마 컨텍스트"""

    generation: QueryGeneration
    """쿼리 생성 상태"""

    validation: ValidationResult
    """검증 결과"""

    execution: ExecutionResult
    """실행 결과"""

    response: ResponseOutput
    """응답 출력"""

    debug: DebugContext
    """디버그 컨텍스트"""

    # 대화 컨텍스트 (add_messages 리듀서 필요로 최상위 유지)
    messages: Annotated[list[BaseMessage], add_messages]
    """대화 히스토리 (add_messages 리듀서로 자동 누적)"""


# === State Update Helpers ===
# LangGraph의 Nested TypedDict는 deep merge가 아닌 replace(전체 교체) 방식으로 동작합니다.
# 아래 헬퍼 함수들은 현재 상태 값을 유지하면서 특정 필드만 안전하게 업데이트합니다.


def update_execution(state: "Text2SQLAgentState", **overrides) -> ExecutionResult:
    """execution 컨텍스트의 현재 값을 유지하면서 특정 필드만 업데이트"""
    current = state.get("execution", {})
    return {
        "query_result": current.get("query_result", []),
        "result_columns": current.get("result_columns", []),
        "total_row_count": current.get("total_row_count", 0),
        "execution_time_ms": current.get("execution_time_ms", 0),
        "execution_error": current.get("execution_error", None),
        **overrides,
    }


def update_response(state: "Text2SQLAgentState", **overrides) -> ResponseOutput:
    """response 컨텍스트의 현재 값을 유지하면서 특정 필드만 업데이트"""
    current = state.get("response", {})
    return {
        "user_approved": current.get("user_approved", None),
        "final_response": current.get("final_response", ""),
        "response_format": current.get("response_format", "table"),
        **overrides,
    }


def update_generation(state: "Text2SQLAgentState", **overrides) -> QueryGeneration:
    """generation 컨텍스트의 현재 값을 유지하면서 특정 필드만 업데이트"""
    current = state.get("generation", {})
    return {
        "generated_query": current.get("generated_query", ""),
        "query_explanation": current.get("query_explanation", ""),
        "generation_attempt": current.get("generation_attempt", 0),
        "query_id": current.get("query_id", ""),
        **overrides,
    }


def update_validation(state: "Text2SQLAgentState", **overrides) -> ValidationResult:
    """validation 컨텍스트의 현재 값을 유지하면서 특정 필드만 업데이트"""
    current = state.get("validation", {})
    return {
        "validation_errors": current.get("validation_errors", []),
        "is_query_valid": current.get("is_query_valid", False),
        **overrides,
    }


def update_schema(state: "Text2SQLAgentState", **overrides) -> SchemaContext:
    """schema 컨텍스트의 현재 값을 유지하면서 특정 필드만 업데이트"""
    current = state.get("schema", {})
    return {
        "database_schema": current.get("database_schema", ""),
        "relevant_tables": current.get("relevant_tables", []),
        **overrides,
    }


# === Helper Functions ===


def create_initial_input(
    user_question: str,
    session_id: str,
    llm_provider: Literal["openai", "anthropic", "google"] = "openai",
) -> InputContext:
    """초기 입력 컨텍스트 생성"""
    return InputContext(
        user_question=user_question,
        session_id=session_id,
        llm_provider=llm_provider,
    )


def create_initial_auth(
    user_id: int | None = None,
    user_roles: list[str] | None = None,
    accessible_tables: list[str] | None = None,
) -> AuthContext:
    """초기 인증 컨텍스트 생성"""
    return AuthContext(
        user_id=user_id,
        user_roles=user_roles or [],
        accessible_tables=accessible_tables or [],
    )


def create_initial_schema() -> SchemaContext:
    """초기 스키마 컨텍스트 생성"""
    return SchemaContext(
        database_schema="",
        relevant_tables=[],
    )


def create_initial_generation() -> QueryGeneration:
    """초기 쿼리 생성 상태 생성"""
    return QueryGeneration(
        generated_query="",
        query_explanation="",
        generation_attempt=0,
        query_id="",
    )


def create_initial_validation() -> ValidationResult:
    """초기 검증 결과 생성"""
    return ValidationResult(
        validation_errors=[],
        is_query_valid=False,
    )


def create_initial_execution() -> ExecutionResult:
    """초기 실행 결과 생성"""
    return ExecutionResult(
        query_result=[],
        result_columns=[],
        total_row_count=0,
        execution_time_ms=0,
        execution_error=None,
    )


def create_initial_response() -> ResponseOutput:
    """초기 응답 출력 생성"""
    return ResponseOutput(
        user_approved=None,
        final_response="",
        response_format="table",
    )


def create_initial_debug(trace_id: str = "") -> DebugContext:
    """초기 디버그 컨텍스트 생성"""
    import uuid

    return DebugContext(
        trace_id=trace_id or str(uuid.uuid4()),
        node_timings=[],
        error_chain=[],
        current_node="",
        retry_history=[],
    )


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
        # 중첩 컨텍스트
        input=create_initial_input(user_question, session_id, llm_provider),
        auth=create_initial_auth(user_id, user_roles, accessible_tables),
        schema=create_initial_schema(),
        generation=create_initial_generation(),
        validation=create_initial_validation(),
        execution=create_initial_execution(),
        response=create_initial_response(),
        debug=create_initial_debug(),
        # 대화 컨텍스트
        messages=[],
    )


# === Backward Compatibility Accessors ===
# 기존 flat 접근 패턴을 지원하는 헬퍼 함수들


def get_user_question(state: Text2SQLAgentState) -> str:
    """user_question 접근 헬퍼"""
    return state["input"]["user_question"]


def get_session_id(state: Text2SQLAgentState) -> str:
    """session_id 접근 헬퍼"""
    return state["input"]["session_id"]


def get_llm_provider(state: Text2SQLAgentState) -> Literal["openai", "anthropic", "google"]:
    """llm_provider 접근 헬퍼"""
    return state["input"]["llm_provider"]


def get_user_id(state: Text2SQLAgentState) -> int | None:
    """user_id 접근 헬퍼"""
    return state["auth"]["user_id"]


def get_user_roles(state: Text2SQLAgentState) -> list[str]:
    """user_roles 접근 헬퍼"""
    return state["auth"]["user_roles"]


def get_accessible_tables(state: Text2SQLAgentState) -> list[str]:
    """accessible_tables 접근 헬퍼"""
    return state["auth"]["accessible_tables"]


def get_database_schema(state: Text2SQLAgentState) -> str:
    """database_schema 접근 헬퍼"""
    return state["schema"]["database_schema"]


def get_relevant_tables(state: Text2SQLAgentState) -> list[str]:
    """relevant_tables 접근 헬퍼"""
    return state["schema"]["relevant_tables"]


def get_generated_query(state: Text2SQLAgentState) -> str:
    """generated_query 접근 헬퍼"""
    return state["generation"]["generated_query"]


def get_query_explanation(state: Text2SQLAgentState) -> str:
    """query_explanation 접근 헬퍼"""
    return state["generation"]["query_explanation"]


def get_generation_attempt(state: Text2SQLAgentState) -> int:
    """generation_attempt 접근 헬퍼"""
    return state["generation"]["generation_attempt"]


def get_query_id(state: Text2SQLAgentState) -> str:
    """query_id 접근 헬퍼"""
    return state["generation"]["query_id"]


def get_validation_errors(state: Text2SQLAgentState) -> list[str]:
    """validation_errors 접근 헬퍼"""
    return state["validation"]["validation_errors"]


def get_is_query_valid(state: Text2SQLAgentState) -> bool:
    """is_query_valid 접근 헬퍼"""
    return state["validation"]["is_query_valid"]


def get_query_result(state: Text2SQLAgentState) -> list[dict[str, object]]:
    """query_result 접근 헬퍼"""
    return state["execution"]["query_result"]


def get_result_columns(state: Text2SQLAgentState) -> list[dict[str, object]]:
    """result_columns 접근 헬퍼"""
    return state["execution"]["result_columns"]


def get_total_row_count(state: Text2SQLAgentState) -> int:
    """total_row_count 접근 헬퍼"""
    return state["execution"]["total_row_count"]


def get_execution_time_ms(state: Text2SQLAgentState) -> int:
    """execution_time_ms 접근 헬퍼"""
    return state["execution"]["execution_time_ms"]


def get_execution_error(state: Text2SQLAgentState) -> str | None:
    """execution_error 접근 헬퍼"""
    return state["execution"]["execution_error"]


def get_user_approved(state: Text2SQLAgentState) -> bool | None:
    """user_approved 접근 헬퍼"""
    return state["response"]["user_approved"]


def get_final_response(state: Text2SQLAgentState) -> str:
    """final_response 접근 헬퍼"""
    return state["response"]["final_response"]


def get_response_format(state: Text2SQLAgentState) -> Literal["table", "summary", "error"]:
    """response_format 접근 헬퍼"""
    return state["response"]["response_format"]


def get_debug_context(state: Text2SQLAgentState) -> DebugContext:
    """debug 접근 헬퍼"""
    return state["debug"]
