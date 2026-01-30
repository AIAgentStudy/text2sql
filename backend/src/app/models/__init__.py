"""
Pydantic 모델 패키지

API 스키마와 엔티티 모델을 제공합니다.
"""

from app.models.entities import (
    ColumnInfo,
    ConversationSession,
    DatabaseSchema,
    ExecutionError,
    ForeignKeyInfo,
    GeneratedQuery,
    LLMProvider,
    Message,
    QueryRequest,
    QueryRequestStatus,
    QueryResult,
    SchemaColumnInfo,
    SessionStatus,
    TableInfo,
    ValidationError,
    ValidationStatus,
)
from app.models.requests import (
    ChatRequest,
    ConfirmationRequest,
    CreateSessionRequest,
)
from app.models.responses import (
    ChatStreamEvent,
    ConfirmationResponse,
    ConfirmRequiredEvent,
    DatabaseSchemaResponse,
    DoneEvent,
    ErrorDetail,
    ErrorEvent,
    ErrorResponse,
    HealthDependencies,
    HealthResponse,
    QueryPreviewEvent,
    QueryResultData,
    ResultEvent,
    SessionEvent,
    SessionResponse,
    StatusEvent,
)

__all__ = [
    # 엔티티
    "ColumnInfo",
    "ConversationSession",
    "DatabaseSchema",
    "ExecutionError",
    "ForeignKeyInfo",
    "GeneratedQuery",
    "LLMProvider",
    "Message",
    "QueryRequest",
    "QueryRequestStatus",
    "QueryResult",
    "SchemaColumnInfo",
    "SessionStatus",
    "TableInfo",
    "ValidationError",
    "ValidationStatus",
    # 요청
    "ChatRequest",
    "ConfirmationRequest",
    "CreateSessionRequest",
    # 응답
    "ChatStreamEvent",
    "ConfirmationResponse",
    "ConfirmRequiredEvent",
    "DatabaseSchemaResponse",
    "DoneEvent",
    "ErrorDetail",
    "ErrorEvent",
    "ErrorResponse",
    "HealthDependencies",
    "HealthResponse",
    "QueryPreviewEvent",
    "QueryResultData",
    "ResultEvent",
    "SessionEvent",
    "SessionResponse",
    "StatusEvent",
]
