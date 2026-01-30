"""
핵심 엔티티 모델 정의

데이터 모델 문서(data-model.md)에 정의된 엔티티들의 Pydantic 모델입니다.
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


# === 열거형 ===


class QueryRequestStatus(str, Enum):
    """쿼리 요청 상태"""

    PENDING = "pending"
    GENERATING = "generating"
    VALIDATING = "validating"
    AWAITING_CONFIRM = "awaiting_confirm"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ValidationStatus(str, Enum):
    """검증 상태"""

    PENDING = "pending"
    VALID = "valid"
    INVALID = "invalid"


class SessionStatus(str, Enum):
    """세션 상태"""

    ACTIVE = "active"
    EXPIRED = "expired"
    TERMINATED = "terminated"


class LLMProvider(str, Enum):
    """LLM 제공자"""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"


# === 기본 엔티티 ===


class Message(BaseModel):
    """대화 메시지"""

    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ConversationSession(BaseModel):
    """대화 세션"""

    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity_at: datetime = Field(default_factory=datetime.utcnow)
    status: SessionStatus = SessionStatus.ACTIVE
    llm_provider: LLMProvider = LLMProvider.OPENAI
    message_history: list[Message] = Field(default_factory=list, max_length=10)


class QueryRequest(BaseModel):
    """쿼리 요청"""

    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    user_question: str = Field(min_length=2, max_length=1000)
    requested_at: datetime = Field(default_factory=datetime.utcnow)
    has_context_reference: bool = False
    status: QueryRequestStatus = QueryRequestStatus.PENDING


class ValidationError(BaseModel):
    """검증 오류"""

    layer: Literal["keyword", "schema", "semantic"]
    code: str
    message: str
    severity: Literal["error", "warning"]


class GeneratedQuery(BaseModel):
    """생성된 쿼리"""

    query_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    request_id: str
    sql_query: str
    explanation: str = Field(min_length=10)
    referenced_tables: list[str] = Field(default_factory=list)
    validation_status: ValidationStatus = ValidationStatus.PENDING
    validation_errors: list[ValidationError] = Field(default_factory=list)
    generation_attempt: int = Field(ge=1, le=3, default=1)
    model_used: str = ""
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class ColumnInfo(BaseModel):
    """컬럼 정보"""

    name: str
    data_type: str
    is_nullable: bool


class ExecutionError(BaseModel):
    """실행 오류"""

    code: str
    message: str
    user_message: str


class QueryResult(BaseModel):
    """쿼리 결과"""

    result_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    query_id: str
    rows: list[dict[str, object]] = Field(default_factory=list)
    total_row_count: int = Field(ge=0, default=0)
    returned_row_count: int = Field(ge=0, default=0)
    columns: list[ColumnInfo] = Field(default_factory=list)
    is_truncated: bool = False
    execution_time_ms: int = Field(ge=0, default=0)
    executed_at: datetime = Field(default_factory=datetime.utcnow)
    error: ExecutionError | None = None


# === 스키마 관련 엔티티 ===


class ForeignKeyInfo(BaseModel):
    """외래키 정보"""

    referenced_table: str
    referenced_column: str


class SchemaColumnInfo(BaseModel):
    """스키마 컬럼 정보"""

    name: str
    data_type: str
    is_nullable: bool
    description: str | None = None
    default_value: str | None = None
    is_primary_key: bool = False
    foreign_key_reference: ForeignKeyInfo | None = None


class TableInfo(BaseModel):
    """테이블 정보"""

    name: str
    description: str | None = None
    columns: list[SchemaColumnInfo] = Field(default_factory=list)
    estimated_row_count: int = 0


class DatabaseSchema(BaseModel):
    """데이터베이스 스키마"""

    version: str = ""
    last_updated_at: datetime = Field(default_factory=datetime.utcnow)
    tables: list[TableInfo] = Field(default_factory=list)
