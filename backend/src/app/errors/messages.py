"""
한국어 에러 메시지 템플릿

모든 에러 코드에 대한 사용자 친화적 한국어 메시지를 정의합니다.
"""

from enum import Enum
from typing import Any


class ErrorCode(str, Enum):
    """에러 코드 정의"""

    # 보안 관련
    DANGEROUS_QUERY = "DANGEROUS_QUERY"

    # 쿼리 관련
    QUERY_TIMEOUT = "QUERY_TIMEOUT"
    QUERY_GENERATION_ERROR = "QUERY_GENERATION_ERROR"
    QUERY_EXECUTION_ERROR = "QUERY_EXECUTION_ERROR"
    AMBIGUOUS_QUERY = "AMBIGUOUS_QUERY"

    # 검증 관련
    VALIDATION_ERROR_KEYWORD = "VALIDATION_ERROR_KEYWORD"
    VALIDATION_ERROR_SCHEMA = "VALIDATION_ERROR_SCHEMA"
    VALIDATION_ERROR_SEMANTIC = "VALIDATION_ERROR_SEMANTIC"

    # 스키마 관련
    SCHEMA_NOT_FOUND = "SCHEMA_NOT_FOUND"
    TABLE_NOT_FOUND = "TABLE_NOT_FOUND"
    COLUMN_NOT_FOUND = "COLUMN_NOT_FOUND"

    # 세션 관련
    SESSION_NOT_FOUND = "SESSION_NOT_FOUND"
    SESSION_EXPIRED = "SESSION_EXPIRED"

    # 연결 관련
    DATABASE_CONNECTION_ERROR = "DATABASE_CONNECTION_ERROR"
    LLM_ERROR = "LLM_ERROR"

    # 결과 관련
    EMPTY_RESULT = "EMPTY_RESULT"
    RESULT_TOO_LARGE = "RESULT_TOO_LARGE"

    # 일반
    INTERNAL_ERROR = "INTERNAL_ERROR"
    CANCELLED = "CANCELLED"


# 에러 메시지 정의
ERROR_MESSAGES: dict[ErrorCode, str] = {
    # 보안 관련
    ErrorCode.DANGEROUS_QUERY: "조회 요청만 가능합니다. 데이터 수정은 지원되지 않습니다.",

    # 쿼리 관련
    ErrorCode.QUERY_TIMEOUT: "쿼리 실행 시간이 너무 깁니다. 더 구체적인 조건을 추가해주세요.",
    ErrorCode.QUERY_GENERATION_ERROR: "죄송합니다. 질문을 이해하지 못했어요. 다르게 표현해 주시겠어요?",
    ErrorCode.QUERY_EXECUTION_ERROR: "쿼리 실행 중 문제가 발생했습니다. 잠시 후 다시 시도해주세요.",
    ErrorCode.AMBIGUOUS_QUERY: "질문이 조금 모호해요. 어떤 데이터를 보고 싶으신지 더 구체적으로 알려주세요.",

    # 검증 관련
    ErrorCode.VALIDATION_ERROR_KEYWORD: "조회(SELECT) 쿼리만 허용됩니다.",
    ErrorCode.VALIDATION_ERROR_SCHEMA: "요청하신 테이블이나 컬럼을 찾을 수 없습니다.",
    ErrorCode.VALIDATION_ERROR_SEMANTIC: "보안상의 이유로 이 쿼리는 실행할 수 없습니다.",

    # 스키마 관련
    ErrorCode.SCHEMA_NOT_FOUND: "데이터베이스 스키마를 불러올 수 없습니다. 잠시 후 다시 시도해주세요.",
    ErrorCode.TABLE_NOT_FOUND: "'{table_name}' 테이블을 찾을 수 없습니다. 테이블 이름을 확인해주세요.",
    ErrorCode.COLUMN_NOT_FOUND: "'{column_name}' 컬럼을 찾을 수 없습니다. 컬럼 이름을 확인해주세요.",

    # 세션 관련
    ErrorCode.SESSION_NOT_FOUND: "세션이 만료되었거나 존재하지 않습니다. 새로운 대화를 시작해주세요.",
    ErrorCode.SESSION_EXPIRED: "세션이 만료되었습니다. 새로운 대화를 시작해주세요.",

    # 연결 관련
    ErrorCode.DATABASE_CONNECTION_ERROR: "현재 데이터를 가져올 수 없습니다. 잠시 후 다시 시도해주세요.",
    ErrorCode.LLM_ERROR: "질문을 처리하는 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",

    # 결과 관련
    ErrorCode.EMPTY_RESULT: "조건에 맞는 데이터가 없습니다.",
    ErrorCode.RESULT_TOO_LARGE: "결과가 너무 많습니다. 더 구체적인 조건을 추가해주세요.",

    # 일반
    ErrorCode.INTERNAL_ERROR: "시스템 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
    ErrorCode.CANCELLED: "사용자가 쿼리 실행을 취소했습니다.",
}

# 에러 제안 (복구 가능한 에러에 대한 힌트)
ERROR_SUGGESTIONS: dict[ErrorCode, str] = {
    ErrorCode.QUERY_TIMEOUT: "예: '지난 한 달간', '상위 10개만' 같은 조건을 추가해보세요.",
    ErrorCode.QUERY_GENERATION_ERROR: "예: '지난달 매출 상위 10개 제품' 처럼 구체적으로 질문해주세요.",
    ErrorCode.AMBIGUOUS_QUERY: "예: '2024년 1월 서울 지역 매출'처럼 기간, 조건을 명확히 해주세요.",
    ErrorCode.EMPTY_RESULT: "다른 조건으로 검색해보시거나, 기간을 넓혀보세요.",
    ErrorCode.RESULT_TOO_LARGE: "날짜 범위를 좁히거나, LIMIT을 추가해보세요.",
    ErrorCode.TABLE_NOT_FOUND: "사용 가능한 테이블: {available_tables}",
    ErrorCode.COLUMN_NOT_FOUND: "사용 가능한 컬럼: {available_columns}",
}

# 도움말 예시 (모호한 쿼리에 대한 예시)
QUERY_EXAMPLES: list[str] = [
    "지난달 매출 상위 10개 제품은?",
    "서울 지역 고객 수는 몇 명이야?",
    "2024년 월별 주문 건수를 보여줘",
    "가장 많이 팔린 카테고리는?",
    "평균 주문 금액이 10만원 이상인 고객은?",
]


def get_error_message(code: ErrorCode, **kwargs: Any) -> str:
    """
    에러 코드에 대한 사용자 메시지 반환

    Args:
        code: 에러 코드
        **kwargs: 템플릿 변수 (예: table_name, column_name)

    Returns:
        사용자 친화적 에러 메시지
    """
    message = ERROR_MESSAGES.get(code, "알 수 없는 오류가 발생했습니다.")

    # 템플릿 변수 치환
    try:
        message = message.format(**kwargs)
    except KeyError:
        # 템플릿 변수가 제공되지 않은 경우 원본 메시지 반환
        pass

    return message


def get_error_suggestion(code: ErrorCode, **kwargs: Any) -> str | None:
    """
    에러 코드에 대한 제안 반환

    Args:
        code: 에러 코드
        **kwargs: 템플릿 변수

    Returns:
        제안 메시지 또는 None
    """
    suggestion = ERROR_SUGGESTIONS.get(code)
    if suggestion:
        try:
            suggestion = suggestion.format(**kwargs)
        except KeyError:
            pass
    return suggestion


def format_error_response(
    code: ErrorCode,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    에러 응답 포맷팅

    Args:
        code: 에러 코드
        context: 추가 컨텍스트 정보

    Returns:
        포맷된 에러 응답 딕셔너리
    """
    context = context or {}

    response: dict[str, Any] = {
        "code": code.value,
        "message": get_error_message(code, **context),
    }

    suggestion = get_error_suggestion(code, **context)
    if suggestion:
        response["suggestion"] = suggestion

    return response


def get_ambiguous_query_help() -> str:
    """
    모호한 쿼리에 대한 도움말 반환

    Returns:
        도움말 메시지 (예시 포함)
    """
    examples = "\n".join(f"  • {ex}" for ex in QUERY_EXAMPLES[:3])
    return f"""질문을 조금 더 구체적으로 해주시면 정확한 결과를 보여드릴 수 있어요.

예를 들어 이렇게 질문해보세요:
{examples}"""


def is_ambiguous_query(query: str) -> bool:
    """
    쿼리가 모호한지 판단

    Args:
        query: 사용자 질문

    Returns:
        모호한지 여부
    """
    # 너무 짧은 쿼리
    if len(query.strip()) < 5:
        return True

    # 모호한 단어만 있는 경우
    ambiguous_words = {"데이터", "뭐", "그거", "아까", "그것", "저거", "이거", "좀", "어떤"}
    words = set(query.split())
    if words.issubset(ambiguous_words | {"보여줘", "알려줘", "조회", "해줘"}):
        return True

    # 명사가 없는 경우 (간단한 휴리스틱)
    action_only_patterns = ["보여줘", "알려줘", "조회해줘", "검색해줘"]
    if query.strip() in action_only_patterns:
        return True

    return False
