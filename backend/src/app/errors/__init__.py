"""
에러 처리 패키지

커스텀 예외와 에러 핸들러를 제공합니다.
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
]
