"""
테이블 접근 권한 관리

역할에 따른 테이블별 읽기/쓰기 권한을 검사합니다.
"""

import logging
from typing import Literal

from app.database.connection import get_connection
from app.models.auth import UserWithRoles

logger = logging.getLogger(__name__)


async def get_accessible_tables(
    user: UserWithRoles,
    permission_type: Literal["read", "write"] = "read",
) -> list[str]:
    """
    사용자가 접근 가능한 테이블 목록 조회

    Args:
        user: 현재 사용자
        permission_type: 권한 유형 ("read" 또는 "write")

    Returns:
        접근 가능한 테이블 이름 목록
    """
    if not user.roles:
        return []

    permission_column = "can_read" if permission_type == "read" else "can_write"

    query = f"""
        SELECT DISTINCT tp.table_name
        FROM table_permissions tp
        JOIN roles r ON tp.role_id = r.id
        WHERE r.name = ANY($1)
        AND tp.{permission_column} = TRUE
        ORDER BY tp.table_name
    """

    try:
        async with get_connection() as conn:
            rows = await conn.fetch(query, user.roles)
            return [row["table_name"] for row in rows]
    except Exception as e:
        logger.error(f"접근 가능 테이블 조회 실패: {e}")
        return []


async def check_table_permission(
    user: UserWithRoles,
    table_name: str,
    permission_type: Literal["read", "write"] = "read",
) -> bool:
    """
    특정 테이블에 대한 접근 권한 확인

    Args:
        user: 현재 사용자
        table_name: 테이블 이름
        permission_type: 권한 유형 ("read" 또는 "write")

    Returns:
        접근 권한 여부
    """
    if not user.roles:
        return False

    permission_column = "can_read" if permission_type == "read" else "can_write"

    query = f"""
        SELECT EXISTS(
            SELECT 1
            FROM table_permissions tp
            JOIN roles r ON tp.role_id = r.id
            WHERE r.name = ANY($1)
            AND tp.table_name = $2
            AND tp.{permission_column} = TRUE
        ) as has_permission
    """

    try:
        async with get_connection() as conn:
            row = await conn.fetchrow(query, user.roles, table_name)
            return row["has_permission"] if row else False
    except Exception as e:
        logger.error(f"테이블 권한 확인 실패: {e}")
        return False


async def check_tables_permission(
    user: UserWithRoles,
    table_names: list[str],
    permission_type: Literal["read", "write"] = "read",
) -> dict[str, bool]:
    """
    여러 테이블에 대한 접근 권한 확인

    Args:
        user: 현재 사용자
        table_names: 테이블 이름 목록
        permission_type: 권한 유형 ("read" 또는 "write")

    Returns:
        테이블별 접근 권한 딕셔너리
    """
    if not user.roles or not table_names:
        return {table: False for table in table_names}

    permission_column = "can_read" if permission_type == "read" else "can_write"

    query = f"""
        SELECT tp.table_name
        FROM table_permissions tp
        JOIN roles r ON tp.role_id = r.id
        WHERE r.name = ANY($1)
        AND tp.table_name = ANY($2)
        AND tp.{permission_column} = TRUE
    """

    try:
        async with get_connection() as conn:
            rows = await conn.fetch(query, user.roles, table_names)
            allowed_tables = {row["table_name"] for row in rows}
            return {table: table in allowed_tables for table in table_names}
    except Exception as e:
        logger.error(f"테이블 권한 확인 실패: {e}")
        return {table: False for table in table_names}


def filter_schema_by_permission(
    schema: dict,
    accessible_tables: list[str],
) -> dict:
    """
    접근 가능한 테이블만 포함하도록 스키마 필터링

    Args:
        schema: 전체 데이터베이스 스키마
        accessible_tables: 접근 가능한 테이블 목록

    Returns:
        필터링된 스키마
    """
    if not schema or "tables" not in schema:
        return schema

    filtered_tables = [
        table for table in schema["tables"]
        if table.get("name") in accessible_tables
    ]

    return {
        **schema,
        "tables": filtered_tables,
    }


def extract_tables_from_query(sql_query: str) -> list[str]:
    """
    SQL 쿼리에서 참조된 테이블 이름 추출

    간단한 파싱으로 FROM, JOIN 절에서 테이블 이름을 추출합니다.
    완벽한 SQL 파서는 아니므로, 복잡한 쿼리에서는 정확하지 않을 수 있습니다.

    Args:
        sql_query: SQL 쿼리 문자열

    Returns:
        추출된 테이블 이름 목록
    """
    import re

    # SQL 키워드 패턴
    sql_upper = sql_query.upper()
    sql_normalized = sql_query

    tables = set()

    # FROM 절에서 테이블 추출
    from_pattern = r'\bFROM\s+([a-zA-Z_][a-zA-Z0-9_]*)'
    for match in re.finditer(from_pattern, sql_upper):
        start = match.start(1)
        end = match.end(1)
        table_name = sql_normalized[start:end].strip()
        tables.add(table_name.lower())

    # JOIN 절에서 테이블 추출
    join_pattern = r'\bJOIN\s+([a-zA-Z_][a-zA-Z0-9_]*)'
    for match in re.finditer(join_pattern, sql_upper):
        start = match.start(1)
        end = match.end(1)
        table_name = sql_normalized[start:end].strip()
        tables.add(table_name.lower())

    # INTO 절에서 테이블 추출 (INSERT)
    into_pattern = r'\bINTO\s+([a-zA-Z_][a-zA-Z0-9_]*)'
    for match in re.finditer(into_pattern, sql_upper):
        start = match.start(1)
        end = match.end(1)
        table_name = sql_normalized[start:end].strip()
        tables.add(table_name.lower())

    # UPDATE 절에서 테이블 추출
    update_pattern = r'\bUPDATE\s+([a-zA-Z_][a-zA-Z0-9_]*)'
    for match in re.finditer(update_pattern, sql_upper):
        start = match.start(1)
        end = match.end(1)
        table_name = sql_normalized[start:end].strip()
        tables.add(table_name.lower())

    return list(tables)


async def validate_query_permission(
    user: UserWithRoles,
    sql_query: str,
) -> tuple[bool, list[str]]:
    """
    SQL 쿼리 실행 권한 검증

    Args:
        user: 현재 사용자
        sql_query: 실행할 SQL 쿼리

    Returns:
        (권한 있음 여부, 권한 없는 테이블 목록)
    """
    # 쿼리에서 테이블 추출
    tables = extract_tables_from_query(sql_query)

    if not tables:
        # 테이블을 추출할 수 없으면 허용 (SELECT 1 같은 쿼리)
        return True, []

    # 쿼리 타입에 따른 권한 유형 결정
    sql_upper = sql_query.strip().upper()
    if sql_upper.startswith(("INSERT", "UPDATE", "DELETE")):
        permission_type = "write"
    else:
        permission_type = "read"

    # 테이블별 권한 확인
    permissions = await check_tables_permission(user, tables, permission_type)

    unauthorized_tables = [
        table for table, has_permission in permissions.items()
        if not has_permission
    ]

    return len(unauthorized_tables) == 0, unauthorized_tables
