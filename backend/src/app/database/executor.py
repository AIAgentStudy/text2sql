"""
안전한 쿼리 실행기

READ ONLY 트랜잭션, 타임아웃, 행 제한을 적용하여 쿼리를 실행합니다.
"""

import logging
import time
from typing import Any

import asyncpg

from app.config import get_settings
from app.database.connection import get_readonly_connection
from app.errors.exceptions import (
    DatabaseConnectionError,
    DangerousQueryError,
    QueryTimeoutError,
)
from app.models.entities import ColumnInfo, QueryResult

logger = logging.getLogger(__name__)

# 위험 키워드 (기본 검사용)
DANGEROUS_KEYWORDS = frozenset(
    {
        "UPDATE",
        "DELETE",
        "INSERT",
        "DROP",
        "ALTER",
        "TRUNCATE",
        "GRANT",
        "REVOKE",
        "CREATE",
        "MODIFY",
        "EXEC",
        "EXECUTE",
    }
)


def _quick_safety_check(query: str) -> None:
    """
    빠른 안전 검사 (키워드 기반)

    Args:
        query: SQL 쿼리

    Raises:
        DangerousQueryError: 위험 키워드 감지 시
    """
    query_upper = query.upper()
    for keyword in DANGEROUS_KEYWORDS:
        # 단어 경계를 고려한 검사
        if f" {keyword} " in f" {query_upper} ":
            raise DangerousQueryError(keyword)


async def execute_safe_query(
    query: str,
    timeout_ms: int | None = None,
    max_rows: int | None = None,
) -> QueryResult:
    """
    안전하게 쿼리를 실행합니다.

    Args:
        query: 실행할 SQL 쿼리
        timeout_ms: 타임아웃 (밀리초)
        max_rows: 최대 반환 행 수

    Returns:
        QueryResult: 쿼리 실행 결과

    Raises:
        DangerousQueryError: 위험한 쿼리 감지 시
        QueryTimeoutError: 타임아웃 발생 시
        DatabaseConnectionError: DB 연결 오류 시
    """
    settings = get_settings()
    timeout = timeout_ms or settings.query_timeout_ms
    max_row_limit = max_rows or settings.max_result_rows

    # 빠른 안전 검사
    _quick_safety_check(query)

    # SELECT로 시작하는지 확인
    query_stripped = query.strip().upper()
    if not query_stripped.startswith("SELECT"):
        raise DangerousQueryError("NON_SELECT")

    logger.debug(f"쿼리 실행: {query[:200]}...")
    start_time = time.time()

    try:
        async with get_readonly_connection(timeout) as conn:
            # 쿼리 실행
            rows = await conn.fetch(query)

            # 실행 시간 계산
            execution_time_ms = int((time.time() - start_time) * 1000)

            # 결과 처리
            total_count = len(rows)
            is_truncated = total_count > max_row_limit

            if is_truncated:
                rows = rows[:max_row_limit]

            # 컬럼 정보 추출
            columns: list[ColumnInfo] = []
            if rows:
                # asyncpg Record에서 컬럼 정보 추출
                for key in rows[0].keys():
                    columns.append(
                        ColumnInfo(
                            name=key,
                            data_type="unknown",  # asyncpg에서 타입 정보 제한적
                            is_nullable=True,
                        )
                    )

            # dict로 변환
            result_rows: list[dict[str, Any]] = [dict(row) for row in rows]

            logger.info(
                f"쿼리 실행 완료: {total_count}행, {execution_time_ms}ms"
            )

            return QueryResult(
                query_id="",  # 호출자가 설정
                rows=result_rows,
                total_row_count=total_count,
                returned_row_count=len(result_rows),
                columns=columns,
                is_truncated=is_truncated,
                execution_time_ms=execution_time_ms,
            )

    except asyncpg.QueryCanceledError as e:
        logger.warning(f"쿼리 타임아웃: {timeout}ms")
        raise QueryTimeoutError(timeout) from e
    except DangerousQueryError:
        raise
    except asyncpg.PostgresError as e:
        logger.error(f"PostgreSQL 오류: {e}")
        raise DatabaseConnectionError(str(e)) from e
    except Exception as e:
        logger.error(f"쿼리 실행 중 예상치 못한 오류: {e}")
        raise DatabaseConnectionError(str(e)) from e
