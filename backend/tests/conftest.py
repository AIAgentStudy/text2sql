"""
pytest 설정 및 공통 fixture

테스트에서 사용하는 공통 설정과 fixture를 정의합니다.
"""

import asyncio
from collections.abc import AsyncGenerator, Generator
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

from app.config import Settings
from app.main import app


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """세션 범위의 이벤트 루프"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_settings() -> Settings:
    """테스트용 설정"""
    return Settings(
        database_url="postgresql://test:test@localhost:5432/test_db",  # type: ignore[arg-type]
        openai_api_key="test-api-key",
        debug=True,
        log_level="DEBUG",
    )


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """동기 테스트 클라이언트"""
    with TestClient(app) as c:
        yield c


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """비동기 테스트 클라이언트"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def mock_db_pool() -> MagicMock:
    """모의 데이터베이스 연결 풀"""
    pool = MagicMock()
    pool.acquire = MagicMock(return_value=AsyncMock())
    return pool


@pytest.fixture
def mock_llm() -> AsyncMock:
    """모의 LLM 모델"""
    llm = AsyncMock()
    llm.ainvoke = AsyncMock(return_value=MagicMock(content="SELECT * FROM users"))
    return llm


@pytest.fixture
def sample_schema() -> dict[str, Any]:
    """샘플 데이터베이스 스키마"""
    return {
        "version": "test123",
        "tables": [
            {
                "name": "users",
                "description": "사용자 정보",
                "columns": [
                    {"name": "id", "data_type": "integer", "is_nullable": False},
                    {"name": "name", "data_type": "varchar", "is_nullable": False},
                    {"name": "email", "data_type": "varchar", "is_nullable": True},
                ],
            },
            {
                "name": "orders",
                "description": "주문 정보",
                "columns": [
                    {"name": "id", "data_type": "integer", "is_nullable": False},
                    {"name": "user_id", "data_type": "integer", "is_nullable": False},
                    {"name": "total", "data_type": "numeric", "is_nullable": False},
                    {"name": "created_at", "data_type": "timestamp", "is_nullable": False},
                ],
            },
        ],
    }


@pytest.fixture
def sample_query_result() -> list[dict[str, Any]]:
    """샘플 쿼리 결과"""
    return [
        {"id": 1, "name": "홍길동", "email": "hong@example.com"},
        {"id": 2, "name": "김철수", "email": "kim@example.com"},
        {"id": 3, "name": "이영희", "email": "lee@example.com"},
    ]
