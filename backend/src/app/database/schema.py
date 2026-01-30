"""
데이터베이스 스키마 추출

PostgreSQL의 information_schema와 pg_catalog에서 스키마 정보를 조회합니다.
"""

import hashlib
import logging
from datetime import datetime, timedelta

from app.database.connection import get_connection
from app.models.entities import (
    DatabaseSchema,
    ForeignKeyInfo,
    SchemaColumnInfo,
    TableInfo,
)

logger = logging.getLogger(__name__)

# 스키마 캐시
_schema_cache: DatabaseSchema | None = None
_cache_updated_at: datetime | None = None
SCHEMA_CACHE_TTL = timedelta(hours=1)


async def get_database_schema(force_refresh: bool = False) -> DatabaseSchema:
    """
    데이터베이스 스키마 정보 조회

    Args:
        force_refresh: True면 캐시를 무시하고 새로 조회

    Returns:
        DatabaseSchema: 스키마 정보
    """
    global _schema_cache, _cache_updated_at

    # 캐시 확인
    if not force_refresh and _schema_cache is not None and _cache_updated_at is not None:
        if datetime.utcnow() - _cache_updated_at < SCHEMA_CACHE_TTL:
            logger.debug("스키마 캐시 사용")
            return _schema_cache

    logger.info("데이터베이스 스키마 조회 시작")

    async with get_connection() as conn:
        # 테이블 및 컬럼 정보 조회
        columns_query = """
            SELECT
                c.table_name,
                c.column_name,
                c.data_type,
                c.is_nullable = 'YES' as is_nullable,
                c.column_default,
                c.ordinal_position
            FROM information_schema.columns c
            JOIN information_schema.tables t
                ON c.table_schema = t.table_schema
                AND c.table_name = t.table_name
            WHERE c.table_schema = 'public'
                AND t.table_type = 'BASE TABLE'
            ORDER BY c.table_name, c.ordinal_position
        """
        columns_rows = await conn.fetch(columns_query)

        # 테이블 설명 조회
        table_comments_query = """
            SELECT
                c.relname as table_name,
                pd.description
            FROM pg_catalog.pg_class c
            JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
            LEFT JOIN pg_catalog.pg_description pd ON pd.objoid = c.oid AND pd.objsubid = 0
            WHERE n.nspname = 'public'
                AND c.relkind = 'r'
        """
        table_comments = await conn.fetch(table_comments_query)
        table_comment_map = {row["table_name"]: row["description"] for row in table_comments}

        # 컬럼 설명 조회
        column_comments_query = """
            SELECT
                c.relname as table_name,
                a.attname as column_name,
                pd.description
            FROM pg_catalog.pg_class c
            JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
            JOIN pg_catalog.pg_attribute a ON a.attrelid = c.oid
            LEFT JOIN pg_catalog.pg_description pd
                ON pd.objoid = c.oid AND pd.objsubid = a.attnum
            WHERE n.nspname = 'public'
                AND c.relkind = 'r'
                AND a.attnum > 0
                AND NOT a.attisdropped
        """
        column_comments = await conn.fetch(column_comments_query)
        column_comment_map = {
            (row["table_name"], row["column_name"]): row["description"]
            for row in column_comments
        }

        # Primary Key 조회
        pk_query = """
            SELECT
                tc.table_name,
                kcu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            WHERE tc.constraint_type = 'PRIMARY KEY'
                AND tc.table_schema = 'public'
        """
        pk_rows = await conn.fetch(pk_query)
        pk_map = {(row["table_name"], row["column_name"]) for row in pk_rows}

        # Foreign Key 조회
        fk_query = """
            SELECT
                tc.table_name,
                kcu.column_name,
                ccu.table_name AS referenced_table,
                ccu.column_name AS referenced_column
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage ccu
                ON ccu.constraint_name = tc.constraint_name
                AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_schema = 'public'
        """
        fk_rows = await conn.fetch(fk_query)
        fk_map = {
            (row["table_name"], row["column_name"]): ForeignKeyInfo(
                referenced_table=row["referenced_table"],
                referenced_column=row["referenced_column"],
            )
            for row in fk_rows
        }

        # 테이블별 예상 행 수 조회
        row_count_query = """
            SELECT
                relname as table_name,
                reltuples::bigint as estimated_row_count
            FROM pg_catalog.pg_class c
            JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = 'public'
                AND c.relkind = 'r'
        """
        row_counts = await conn.fetch(row_count_query)
        row_count_map = {
            row["table_name"]: max(0, row["estimated_row_count"]) for row in row_counts
        }

    # 테이블별로 그룹화
    tables_dict: dict[str, list[SchemaColumnInfo]] = {}
    for row in columns_rows:
        table_name = row["table_name"]
        column_name = row["column_name"]

        column_info = SchemaColumnInfo(
            name=column_name,
            data_type=row["data_type"],
            is_nullable=row["is_nullable"],
            description=column_comment_map.get((table_name, column_name)),
            default_value=row["column_default"],
            is_primary_key=(table_name, column_name) in pk_map,
            foreign_key_reference=fk_map.get((table_name, column_name)),
        )

        if table_name not in tables_dict:
            tables_dict[table_name] = []
        tables_dict[table_name].append(column_info)

    # TableInfo 목록 생성
    tables = [
        TableInfo(
            name=table_name,
            description=table_comment_map.get(table_name),
            columns=columns,
            estimated_row_count=row_count_map.get(table_name, 0),
        )
        for table_name, columns in sorted(tables_dict.items())
    ]

    # 버전 해시 생성 (스키마 변경 감지용)
    schema_str = str([(t.name, [c.name for c in t.columns]) for t in tables])
    version = hashlib.md5(schema_str.encode()).hexdigest()[:8]

    # 캐시 업데이트
    _schema_cache = DatabaseSchema(
        version=version,
        last_updated_at=datetime.utcnow(),
        tables=tables,
    )
    _cache_updated_at = datetime.utcnow()

    logger.info(f"스키마 조회 완료: {len(tables)}개 테이블, 버전 {version}")
    return _schema_cache


def format_schema_for_llm(schema: DatabaseSchema) -> str:
    """
    LLM 프롬프트용 스키마 문자열 생성

    Args:
        schema: 데이터베이스 스키마

    Returns:
        str: LLM에 전달할 스키마 설명 문자열
    """
    lines = ["## 데이터베이스 스키마", ""]

    for table in schema.tables:
        # 테이블 헤더
        table_desc = f" - {table.description}" if table.description else ""
        lines.append(f"### 테이블: {table.name}{table_desc}")

        # 컬럼 목록
        lines.append("| 컬럼명 | 타입 | NULL 허용 | 설명 |")
        lines.append("|--------|------|-----------|------|")

        for col in table.columns:
            nullable = "예" if col.is_nullable else "아니오"
            pk_marker = " (PK)" if col.is_primary_key else ""
            fk_marker = ""
            if col.foreign_key_reference:
                fk = col.foreign_key_reference
                fk_marker = f" → {fk.referenced_table}.{fk.referenced_column}"
            desc = col.description or ""
            lines.append(
                f"| {col.name}{pk_marker}{fk_marker} | {col.data_type} | {nullable} | {desc} |"
            )

        lines.append("")

    return "\n".join(lines)


def clear_schema_cache() -> None:
    """스키마 캐시 초기화"""
    global _schema_cache, _cache_updated_at
    _schema_cache = None
    _cache_updated_at = None
    logger.info("스키마 캐시 초기화됨")
