"""
데이터베이스 연결 관리

asyncpg를 사용한 PostgreSQL 비동기 연결 풀 관리입니다.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import asyncpg

from app.config import Settings, get_settings
from app.errors.exceptions import DatabaseConnectionError

logger = logging.getLogger(__name__)

# 전역 연결 풀
_pool: asyncpg.Pool | None = None


async def create_pool(settings: Settings | None = None) -> asyncpg.Pool:
    """데이터베이스 연결 풀 생성"""
    global _pool

    if _pool is not None:
        return _pool

    if settings is None:
        settings = get_settings()

    try:
        _pool = await asyncpg.create_pool(
            dsn=settings.database_url_str,
            min_size=settings.db_pool_min_size,
            max_size=settings.db_pool_max_size,
            command_timeout=settings.query_timeout_ms / 1000,  # 초 단위
        )
        logger.info("데이터베이스 연결 풀 생성 완료")
        return _pool
    except Exception as e:
        logger.error(f"데이터베이스 연결 풀 생성 실패: {e}")
        raise DatabaseConnectionError(str(e)) from e


async def close_pool() -> None:
    """데이터베이스 연결 풀 종료"""
    global _pool

    if _pool is not None:
        await _pool.close()
        _pool = None
        logger.info("데이터베이스 연결 풀 종료")


def get_pool() -> asyncpg.Pool:
    """현재 연결 풀 반환"""
    if _pool is None:
        raise DatabaseConnectionError("연결 풀이 초기화되지 않았습니다.")
    return _pool


@asynccontextmanager
async def get_connection() -> AsyncGenerator[asyncpg.Connection, None]:
    """연결 풀에서 연결 획득 (컨텍스트 매니저)"""
    pool = get_pool()
    try:
        async with pool.acquire() as connection:
            yield connection
    except asyncpg.PostgresError as e:
        logger.error(f"데이터베이스 연결 오류: {e}")
        raise DatabaseConnectionError(str(e)) from e


@asynccontextmanager
async def get_readonly_connection(
    timeout_ms: int | None = None,
) -> AsyncGenerator[asyncpg.Connection, None]:
    """
    읽기 전용 연결 획득

    트랜잭션을 READ ONLY로 설정하고, 타임아웃을 적용합니다.
    """
    settings = get_settings()
    timeout = timeout_ms or settings.query_timeout_ms

    async with get_connection() as conn:
        try:
            # 읽기 전용 트랜잭션 시작
            await conn.execute("SET TRANSACTION READ ONLY")
            # 쿼리 타임아웃 설정
            await conn.execute(f"SET statement_timeout = {timeout}")
            yield conn
        except asyncpg.PostgresError as e:
            logger.error(f"읽기 전용 연결 설정 오류: {e}")
            raise DatabaseConnectionError(str(e)) from e


async def check_connection() -> bool:
    """데이터베이스 연결 상태 확인"""
    try:
        async with get_connection() as conn:
            result = await conn.fetchval("SELECT 1")
            return result == 1
    except Exception as e:
        logger.warning(f"데이터베이스 연결 확인 실패: {e}")
        return False
