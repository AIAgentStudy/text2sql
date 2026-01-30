# Data Model: Text2SQL Agent

**Feature**: Text2SQL Agent
**Date**: 2025-01-30

## Entity Overview

```
┌─────────────────┐       ┌─────────────────┐
│ ConversationSession │◄──────│   QueryRequest   │
└────────┬────────┘       └────────┬────────┘
         │                         │
         │                         ▼
         │                ┌─────────────────┐
         │                │  GeneratedQuery  │
         │                └────────┬────────┘
         │                         │
         │                         ▼
         │                ┌─────────────────┐
         │                │   QueryResult    │
         │                └─────────────────┘
         │
         ▼
┌─────────────────┐
│  DatabaseSchema  │
└─────────────────┘
```

## Entities (Pydantic Models)

### 1. ConversationSession

대화 세션을 나타내며, 사용자의 연속적인 질문들을 그룹화.

```python
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field
import uuid

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
    status: Literal["active", "expired", "terminated"] = "active"
    llm_provider: Literal["openai", "anthropic", "google"] = "openai"
    message_history: list[Message] = Field(default_factory=list, max_length=10)
```

**Validation Rules**:
- `session_id`: UUID v4 형식
- `last_activity_at`: 30분 이상 경과 시 `status` → `expired`
- `message_history`: 최대 10개, 초과 시 오래된 메시지 제거

**State Transitions**:
```
active ──[30분 비활동]──► expired
active ──[사용자 종료]──► terminated
expired ──[재접속]──► active (새 세션 생성)
```

### 2. QueryRequest

사용자의 자연어 질문 요청.

```python
from enum import Enum

class QueryRequestStatus(str, Enum):
    PENDING = "pending"
    GENERATING = "generating"
    VALIDATING = "validating"
    AWAITING_CONFIRM = "awaiting_confirm"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class QueryRequest(BaseModel):
    """쿼리 요청"""
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    user_question: str = Field(min_length=2, max_length=1000)
    requested_at: datetime = Field(default_factory=datetime.utcnow)
    has_context_reference: bool = False
    status: QueryRequestStatus = QueryRequestStatus.PENDING
```

**Validation Rules**:
- `user_question`: 최소 2자, 최대 1000자
- `user_question`: 빈 문자열 또는 공백만 있는 경우 거부

**State Transitions**:
```
pending ──► generating ──► validating ──► awaiting_confirm ──► executing ──► completed
                │              │              │                    │
                ▼              ▼              ▼                    ▼
              failed         failed       cancelled             failed
```

### 3. GeneratedQuery

LLM이 생성한 SQL 쿼리와 메타데이터.

```python
class ValidationStatus(str, Enum):
    PENDING = "pending"
    VALID = "valid"
    INVALID = "invalid"

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
    generation_attempt: int = Field(ge=1, le=3)
    model_used: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
```

**Validation Rules**:
- `sql_query`: SELECT로 시작해야 함 (대소문자 무관)
- `sql_query`: UPDATE, DELETE, INSERT, DROP, ALTER, TRUNCATE 포함 시 즉시 거부
- `generation_attempt`: 최대 3, 초과 시 실패 처리
- `explanation`: 한국어, 최소 10자

### 4. QueryResult

쿼리 실행 결과.

```python
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
    rows: list[dict] = Field(default_factory=list, max_length=10000)
    total_row_count: int = Field(ge=0)
    returned_row_count: int = Field(ge=0, le=10000)
    columns: list[ColumnInfo] = Field(default_factory=list)
    is_truncated: bool = False
    execution_time_ms: int = Field(ge=0)
    executed_at: datetime = Field(default_factory=datetime.utcnow)
    error: ExecutionError | None = None
```

**Validation Rules**:
- `rows`: 최대 10,000행, 초과 시 `is_truncated: True`
- `execution_time_ms`: 30,000ms 초과 시 타임아웃 오류
- 페이지네이션: 기본 100행, 최대 1,000행

### 5. DatabaseSchema

데이터베이스 스키마 메타데이터 (캐싱용).

```python
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
    version: str
    last_updated_at: datetime = Field(default_factory=datetime.utcnow)
    tables: list[TableInfo] = Field(default_factory=list)
```

**Caching Rules**:
- TTL: 1시간
- 수동 갱신: API 엔드포인트 제공
- 버전 해시: 테이블/컬럼 목록 기반

## LangGraph Agent State

LangGraph 워크플로우에서 사용하는 통합 상태.

```python
from typing import TypedDict, Annotated, Literal
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage

class Text2SQLAgentState(TypedDict):
    """Agent 상태 정의"""
    # === 입력 ===
    user_question: str
    session_id: str

    # === 대화 컨텍스트 ===
    messages: Annotated[list[BaseMessage], add_messages]

    # === 스키마 컨텍스트 ===
    database_schema: str
    relevant_tables: list[str]

    # === 쿼리 생성 ===
    generated_query: str
    query_explanation: str
    generation_attempt: int

    # === 검증 ===
    validation_errors: list[str]
    is_query_valid: bool

    # === 사용자 확인 (Human-in-the-Loop) ===
    user_approved: bool | None

    # === 실행 결과 ===
    query_result: list[dict]
    execution_error: str | None

    # === 최종 응답 ===
    final_response: str
    response_format: Literal["table", "summary", "error"]
```

## API Request/Response Types (Pydantic)

### Chat Request

```python
class ChatRequest(BaseModel):
    """채팅 요청"""
    session_id: str | None = None  # 없으면 새 세션 생성
    message: str = Field(min_length=2, max_length=1000)
    llm_provider: Literal["openai", "anthropic", "google"] = "openai"
```

### Chat Response (Streaming Events)

```python
from typing import Union

class SessionEvent(BaseModel):
    type: Literal["session"] = "session"
    session_id: str

class StatusEvent(BaseModel):
    type: Literal["status"] = "status"
    status: QueryRequestStatus
    message: str | None = None

class QueryPreviewEvent(BaseModel):
    type: Literal["query_preview"] = "query_preview"
    query: str
    explanation: str

class ConfirmRequiredEvent(BaseModel):
    type: Literal["confirm_required"] = "confirm_required"
    query_id: str

class ResultEvent(BaseModel):
    type: Literal["result"] = "result"
    data: QueryResult

class ErrorEvent(BaseModel):
    type: Literal["error"] = "error"
    error: ExecutionError

class DoneEvent(BaseModel):
    type: Literal["done"] = "done"

ChatStreamEvent = Union[
    SessionEvent,
    StatusEvent,
    QueryPreviewEvent,
    ConfirmRequiredEvent,
    ResultEvent,
    ErrorEvent,
    DoneEvent,
]
```

### Confirmation Request

```python
class ConfirmationRequest(BaseModel):
    """쿼리 실행 확인 요청"""
    session_id: str
    query_id: str
    approved: bool
```

### Confirmation Response

```python
class ConfirmationResponse(BaseModel):
    """쿼리 실행 확인 응답"""
    success: bool
    result: QueryResult | None = None
    error: ExecutionError | None = None
```

## Session State Persistence

LangGraph 체크포인터를 통한 세션 상태 저장.

```python
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

# 개발 환경: 메모리 저장
dev_checkpointer = MemorySaver()

# 프로덕션 환경: PostgreSQL 저장
async def create_prod_checkpointer(connection_string: str):
    return await AsyncPostgresSaver.from_conn_string(connection_string)
```
