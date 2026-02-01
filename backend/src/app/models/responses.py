"""
API 응답 모델 정의

OpenAPI 계약(contracts/api.yaml)에 정의된 응답 스키마들입니다.
"""

from datetime import datetime
from typing import Literal, Union

from pydantic import BaseModel, Field

from app.models.entities import (
    ColumnInfo,
    Message,
    QueryRequestStatus,
    SchemaColumnInfo,
    SessionStatus,
    TableInfo,
)


# === SSE 스트리밍 이벤트 ===


class SessionEvent(BaseModel):
    """세션 이벤트"""

    type: Literal["session"] = "session"
    session_id: str


class StatusEvent(BaseModel):
    """상태 이벤트"""

    type: Literal["status"] = "status"
    status: QueryRequestStatus
    message: str | None = None


class QueryPreviewEvent(BaseModel):
    """쿼리 미리보기 이벤트"""

    type: Literal["query_preview"] = "query_preview"
    query: str = Field(description="생성된 SQL 쿼리")
    explanation: str = Field(description="쿼리에 대한 한국어 설명")


class ConfirmRequiredEvent(BaseModel):
    """확인 필요 이벤트 (간단 버전)"""

    type: Literal["confirm_required"] = "confirm_required"
    query_id: str = Field(description="확인이 필요한 쿼리 ID")


class ConfirmationRequiredEvent(BaseModel):
    """확인 필요 이벤트 (상세 버전)"""

    type: Literal["confirmation_required"] = "confirmation_required"
    query_id: str = Field(description="확인이 필요한 쿼리 ID")
    query: str = Field(description="실행할 SQL 쿼리")
    explanation: str = Field(description="쿼리에 대한 한국어 설명")


class QueryResultData(BaseModel):
    """쿼리 결과 데이터"""

    rows: list[dict[str, object]] = Field(default_factory=list)
    total_row_count: int = Field(ge=0)
    returned_row_count: int = Field(ge=0)
    columns: list[ColumnInfo] = Field(default_factory=list)
    is_truncated: bool = False
    execution_time_ms: int = Field(ge=0)


class ResultEvent(BaseModel):
    """결과 이벤트"""

    type: Literal["result"] = "result"
    data: QueryResultData


class ErrorDetail(BaseModel):
    """에러 상세 정보"""

    code: str
    message: str = Field(description="사용자 친화적 에러 메시지 (한국어)")


class ErrorEvent(BaseModel):
    """에러 이벤트"""

    type: Literal["error"] = "error"
    error: ErrorDetail


class DoneEvent(BaseModel):
    """완료 이벤트"""

    type: Literal["done"] = "done"
    awaiting_confirmation: bool = Field(
        default=False,
        description="True면 사용자 확인 대기 중 (Human-in-the-Loop)",
    )


# SSE 이벤트 유니온 타입
ChatStreamEvent = Union[
    SessionEvent,
    StatusEvent,
    QueryPreviewEvent,
    ConfirmRequiredEvent,
    ConfirmationRequiredEvent,
    ResultEvent,
    ErrorEvent,
    DoneEvent,
]


# === 일반 응답 ===


class ConfirmationResponse(BaseModel):
    """쿼리 실행 확인 응답"""

    success: bool
    result: QueryResultData | None = None
    error: ErrorDetail | None = None


class SessionResponse(BaseModel):
    """세션 응답"""

    session_id: str
    status: SessionStatus
    llm_provider: Literal["openai", "anthropic", "google"] = "openai"
    created_at: datetime
    last_activity_at: datetime
    message_history: list[Message] = Field(default_factory=list, max_length=10)


class DatabaseSchemaResponse(BaseModel):
    """데이터베이스 스키마 응답"""

    version: str
    last_updated_at: datetime
    tables: list[TableInfo] = Field(default_factory=list)


class TableInfoResponse(BaseModel):
    """테이블 정보 응답"""

    name: str
    description: str | None = None
    columns: list[SchemaColumnInfo] = Field(default_factory=list)
    estimated_row_count: int = 0


class HealthDependencies(BaseModel):
    """헬스체크 의존성 상태"""

    database: Literal["ok", "error"]
    llm: Literal["ok", "error"]


class HealthResponse(BaseModel):
    """헬스체크 응답"""

    status: Literal["healthy", "degraded", "unhealthy"]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    dependencies: HealthDependencies | None = None


class ErrorResponse(BaseModel):
    """에러 응답"""

    error: ErrorDetail
