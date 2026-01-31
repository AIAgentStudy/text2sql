"""
에러 처리 패키지

커스텀 예외, 에러 핸들러, 사용자 친화적 메시지를 제공합니다.
"""

from app.errors.exceptions import (
    DatabaseConnectionError,
    DangerousQueryError,
    EmptyResultError,
    LLMError,
    QueryGenerationError,
    QueryTimeoutError,
    QueryValidationError,
    SchemaNotFoundError,
    SessionExpiredError,
    SessionNotFoundError,
    Text2SQLError,
)
from app.errors.handlers import register_error_handlers
from app.errors.messages import (
    ErrorCode,
    ERROR_MESSAGES,
    ERROR_SUGGESTIONS,
    format_error_response,
    get_ambiguous_query_help,
    get_error_message,
    get_error_suggestion,
    is_ambiguous_query,
)

__all__ = [
    # 예외
    "DatabaseConnectionError",
    "DangerousQueryError",
    "EmptyResultError",
    "LLMError",
    "QueryGenerationError",
    "QueryTimeoutError",
    "QueryValidationError",
    "SchemaNotFoundError",
    "SessionExpiredError",
    "SessionNotFoundError",
    "Text2SQLError",
    # 핸들러
    "register_error_handlers",
    # 메시지
    "ErrorCode",
    "ERROR_MESSAGES",
    "ERROR_SUGGESTIONS",
    "format_error_response",
    "get_ambiguous_query_help",
    "get_error_message",
    "get_error_suggestion",
    "is_ambiguous_query",
]
