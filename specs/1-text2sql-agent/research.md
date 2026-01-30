# Research: Text2SQL Agent

**Feature**: Text2SQL Agent
**Date**: 2025-01-30
**Status**: Complete

## 1. LangGraph Agent Architecture (Python)

### Decision: StateGraph with TypedDict State Management

**Rationale**: LangGraph (Python)의 `StateGraph`와 `TypedDict` 기반 상태 관리가 Python 타입 힌트와 완벽히 호환되고, `interrupt()` 함수로 Human-in-the-Loop를 네이티브 지원.

**Alternatives Considered**:
- LangChain AgentExecutor: 덜 유연한 워크플로우 제어, Human-in-the-Loop 지원 제한적
- 커스텀 상태 머신: 추가 구현 비용, LangGraph가 이미 제공하는 기능 중복

### Core Architecture Pattern

```python
from typing import TypedDict, Annotated, Literal
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage

class Text2SQLState(TypedDict):
    """Agent 상태 정의"""
    # 입력
    user_question: str
    session_id: str

    # 대화 컨텍스트 (메시지 누적)
    messages: Annotated[list[BaseMessage], add_messages]

    # 스키마 컨텍스트
    database_schema: str
    relevant_tables: list[str]

    # 쿼리 생성
    generated_query: str
    query_explanation: str
    generation_attempt: int

    # 검증
    validation_errors: list[str]
    is_query_valid: bool

    # 사용자 확인 (Human-in-the-Loop)
    user_approved: bool | None

    # 실행 결과
    query_result: list[dict]
    execution_error: str | None

    # 최종 응답
    final_response: str
    response_format: Literal["table", "summary", "error"]
```

### Graph Flow

```
┌─────────────┐
│   START     │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│ Schema Retrieval│
└────────┬────────┘
         │
         ▼
┌─────────────────┐     실패 (최대 3회)
│ Query Generation│◄────────────────┐
└────────┬────────┘                 │
         │                          │
         ▼                          │
┌─────────────────┐    유효하지 않음│
│ Query Validation├─────────────────┘
└────────┬────────┘
         │ 유효함
         ▼
┌─────────────────┐
│ User Confirm    │──── interrupt() ────► [사용자 입력 대기]
│ (Human-in-Loop) │
└────────┬────────┘
         │ 승인됨
         ▼
┌─────────────────┐
│ Query Execution │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Response Format │
└────────┬────────┘
         │
         ▼
┌─────────────┐
│    END      │
└─────────────┘
```

## 2. Multi-LLM Provider Integration (Python)

### Decision: Protocol-based Abstraction with Factory Pattern

**Rationale**: Python Protocol을 사용하여 타입 안전한 추상화 제공, LangChain의 `BaseChatModel`을 활용하여 팩토리 패턴으로 런타임 프로바이더 전환 지원.

```python
from typing import Protocol, Literal
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI

LLMProvider = Literal["openai", "anthropic", "google"]

class LLMConfig(Protocol):
    provider: LLMProvider
    model_name: str
    temperature: float

def create_llm(config: LLMConfig) -> BaseChatModel:
    """LLM 인스턴스 생성 팩토리"""
    match config.provider:
        case "openai":
            return ChatOpenAI(
                model=config.model_name,
                temperature=config.temperature,
            )
        case "anthropic":
            return ChatAnthropic(
                model=config.model_name,
                temperature=config.temperature,
            )
        case "google":
            return ChatGoogleGenerativeAI(
                model=config.model_name,
                temperature=config.temperature,
            )
        case _:
            raise ValueError(f"Unknown provider: {config.provider}")
```

**Model Selection by Use Case**:
| 용도 | OpenAI | Anthropic | Google |
|------|--------|-----------|--------|
| 쿼리 생성 | gpt-4o | claude-3-5-sonnet-latest | gemini-1.5-pro |
| 검증 (빠른) | gpt-4o-mini | claude-3-5-haiku-latest | gemini-1.5-flash |

## 3. SQL Query Validation Strategy

### Decision: 3-Layer Progressive Validation

**Rationale**: 빠른 검증부터 비용이 높은 검증까지 순차 실행하여 효율성 확보. 위험 쿼리는 첫 레이어에서 즉시 차단.

### Layer 1: Keyword-based Safety Check (O(1))

```python
from dataclasses import dataclass

DANGEROUS_KEYWORDS: frozenset[str] = frozenset({
    'UPDATE', 'DELETE', 'INSERT', 'DROP', 'ALTER', 'TRUNCATE',
    'GRANT', 'REVOKE', 'CREATE', 'MODIFY', 'EXEC', 'EXECUTE'
})

@dataclass
class ValidationResult:
    is_valid: bool
    error: str | None = None

def validate_keywords(query: str) -> ValidationResult:
    """Layer 1: 위험 키워드 검사"""
    query_upper = query.upper()
    for keyword in DANGEROUS_KEYWORDS:
        if keyword in query_upper:
            return ValidationResult(
                is_valid=False,
                error=f"위험한 쿼리 감지: {keyword} 명령어는 사용할 수 없습니다."
            )
    return ValidationResult(is_valid=True)
```

### Layer 2: Schema Validation

```python
async def validate_schema(
    query: str,
    schema: DatabaseSchema
) -> ValidationResult:
    """Layer 2: 스키마 검증 - 테이블/컬럼 존재 확인"""
    tables = extract_table_names(query)
    valid_tables = {t.name for t in schema.tables}

    for table in tables:
        if table not in valid_tables:
            return ValidationResult(
                is_valid=False,
                error=f'테이블 "{table}"을(를) 찾을 수 없습니다.'
            )
    return ValidationResult(is_valid=True)
```

### Layer 3: LLM Semantic Validation

```python
async def validate_semantic(
    query: str,
    llm: BaseChatModel
) -> ValidationResult:
    """Layer 3: LLM 기반 시맨틱 검증"""
    prompt = f"""Check this SQL for common mistakes:
{query}

Check for:
- NULL handling in NOT IN clauses
- Type mismatches in WHERE conditions
- Missing JOINs
- Ambiguous column references

Respond only with "VALID" or list issues."""

    response = await llm.ainvoke(prompt)

    if "VALID" in str(response.content):
        return ValidationResult(is_valid=True)
    return ValidationResult(is_valid=False, error=str(response.content))
```

## 4. Human-in-the-Loop Pattern (Python)

### Decision: LangGraph interrupt() with MemorySaver Checkpointer

**Rationale**: LangGraph 내장 기능 활용으로 세션 지속성과 실행 중단/재개가 자동 처리됨.

```python
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt, Command

def user_confirmation_node(state: Text2SQLState) -> dict:
    """사용자 확인 노드 - Human-in-the-Loop"""
    response = interrupt({
        "query": state["generated_query"],
        "explanation": state["query_explanation"],
        "message": "이 쿼리를 실행할까요?"
    })

    return {"user_approved": response.get("approved", False)}

# 그래프 컴파일 시 checkpointer 설정
checkpointer = MemorySaver()
graph = graph_builder.compile(checkpointer=checkpointer)

# 실행 (중단점까지)
config = {"configurable": {"thread_id": session_id}}
await graph.ainvoke({"user_question": question}, config)

# 사용자 승인 후 재개
await graph.ainvoke(Command(resume={"approved": True}), config)
```

## 5. Session & Conversation Memory

### Decision: Thread-based Persistence + Message Reducer

**Rationale**: LangGraph의 thread_id 기반 체크포인팅으로 세션 복구 지원, 메시지는 `add_messages` reducer로 자동 누적.

```python
from langgraph.graph.message import add_messages

class Text2SQLState(TypedDict):
    # add_messages reducer가 자동으로 메시지 누적 처리
    messages: Annotated[list[BaseMessage], add_messages]

# 세션 타임아웃은 FastAPI 미들웨어에서 관리 (30분)
```

## 6. Database Schema Extraction

### Decision: PostgreSQL information_schema + pg_catalog 직접 조회

**Rationale**: 실시간 스키마 정보 반영, 별도 설정 파일 관리 불필요.

```python
import asyncpg
from functools import lru_cache
from datetime import datetime, timedelta

SCHEMA_CACHE_TTL = timedelta(hours=1)

async def get_postgres_schema(pool: asyncpg.Pool) -> DatabaseSchema:
    """PostgreSQL 스키마 정보 조회"""
    tables_query = """
        SELECT table_name, column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_schema = 'public'
        ORDER BY table_name, ordinal_position
    """

    comments_query = """
        SELECT c.table_name, c.column_name,
               pgd.description as column_comment
        FROM information_schema.columns c
        LEFT JOIN pg_catalog.pg_description pgd
          ON pgd.objsubid = c.ordinal_position
        WHERE c.table_schema = 'public'
    """

    async with pool.acquire() as conn:
        tables = await conn.fetch(tables_query)
        comments = await conn.fetch(comments_query)

    return merge_schema_with_comments(tables, comments)
```

## 7. Safe Query Execution

### Decision: Readonly Connection + Timeout + Result Limit

**Rationale**: 다중 방어 전략으로 데이터 무결성과 시스템 안정성 보장.

```python
import asyncpg
from contextlib import asynccontextmanager

@asynccontextmanager
async def safe_readonly_connection(pool: asyncpg.Pool, timeout_ms: int = 30000):
    """안전한 읽기 전용 연결"""
    async with pool.acquire() as conn:
        await conn.execute('SET TRANSACTION READ ONLY')
        await conn.execute(f'SET statement_timeout = {timeout_ms}')
        yield conn

async def execute_safe_query(
    query: str,
    pool: asyncpg.Pool,
    timeout_ms: int = 30000,
    max_rows: int = 10000
) -> QueryResult:
    """안전한 쿼리 실행"""
    async with safe_readonly_connection(pool, timeout_ms) as conn:
        rows = await conn.fetch(query)

        truncated = len(rows) > max_rows
        if truncated:
            rows = rows[:max_rows]

        return QueryResult(
            rows=[dict(r) for r in rows],
            total_row_count=len(rows),
            is_truncated=truncated
        )
```

## 8. Error Handling Strategy

### Decision: Custom Exception Classes with User-Friendly Messages

```python
from abc import ABC, abstractmethod
from typing import Literal

class Text2SQLError(Exception, ABC):
    """Base exception for Text2SQL agent"""

    @property
    @abstractmethod
    def code(self) -> str: ...

    @property
    @abstractmethod
    def user_message(self) -> str: ...

    @property
    @abstractmethod
    def severity(self) -> Literal["user", "system", "security"]: ...

class DangerousQueryError(Text2SQLError):
    """위험한 쿼리 감지 시 발생"""

    def __init__(self, keyword: str):
        self.keyword = keyword
        super().__init__(f"Dangerous keyword detected: {keyword}")

    @property
    def code(self) -> str:
        return "DANGEROUS_QUERY"

    @property
    def user_message(self) -> str:
        return "조회 요청만 가능합니다. 데이터 수정은 지원되지 않습니다."

    @property
    def severity(self) -> Literal["user", "system", "security"]:
        return "security"

class QueryTimeoutError(Text2SQLError):
    """쿼리 타임아웃 시 발생"""

    @property
    def code(self) -> str:
        return "QUERY_TIMEOUT"

    @property
    def user_message(self) -> str:
        return "쿼리 실행 시간이 너무 깁니다. 더 구체적인 조건을 추가해주세요."

    @property
    def severity(self) -> Literal["user", "system", "security"]:
        return "user"
```

## 9. FastAPI Integration

### Decision: SSE Streaming with StreamingResponse

**Rationale**: LangGraph의 스트리밍 출력을 활용하여 사용자에게 실시간 피드백 제공.

```python
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse
import json

app = FastAPI()

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest) -> EventSourceResponse:
    """채팅 엔드포인트 - SSE 스트리밍"""

    async def event_generator():
        config = {"configurable": {"thread_id": request.session_id}}

        async for event in graph.astream_events(
            {"user_question": request.message},
            config,
            version="v2"
        ):
            if event["event"] == "on_chain_end":
                yield {
                    "event": "message",
                    "data": json.dumps(event["data"], ensure_ascii=False)
                }

        yield {"event": "done", "data": ""}

    return EventSourceResponse(event_generator())
```

## 10. Dependencies Summary

### Backend (Python)
| Package | Version | Purpose |
|---------|---------|---------|
| langgraph | ^0.2.x | Agent 워크플로우 |
| langchain | ^0.3.x | LangChain 코어 |
| langchain-openai | ^0.2.x | OpenAI 통합 |
| langchain-anthropic | ^0.2.x | Anthropic 통합 |
| langchain-google-genai | ^2.x | Google 통합 |
| asyncpg | ^0.29.x | PostgreSQL 비동기 클라이언트 |
| fastapi | ^0.115.x | API 서버 |
| pydantic | ^2.x | 데이터 검증 |
| sse-starlette | ^2.x | Server-Sent Events |
| uvicorn | ^0.32.x | ASGI 서버 |

### Frontend (TypeScript - 변경 없음)
| Package | Version | Purpose |
|---------|---------|---------|
| react | ^18.x | UI 프레임워크 |
| @tanstack/react-query | ^5.x | 서버 상태 관리 |
| tailwindcss | ^3.x | 스타일링 |

### Development
| Package | Version | Purpose |
|---------|---------|---------|
| pytest | ^8.x | 테스트 프레임워크 |
| pytest-asyncio | ^0.24.x | 비동기 테스트 |
| mypy | ^1.x | 타입 체킹 |
| ruff | ^0.8.x | 린팅 및 포매팅 |
