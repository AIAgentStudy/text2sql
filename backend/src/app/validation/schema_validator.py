"""
스키마 기반 SQL 쿼리 검증기 (2단계)

쿼리에서 참조하는 테이블과 컬럼이 실제 스키마에 존재하는지 검증합니다.
"""

import re
from dataclasses import dataclass, field

from app.models.entities import DatabaseSchema


@dataclass
class SchemaValidationResult:
    """스키마 검증 결과"""

    is_valid: bool
    """검증 통과 여부"""

    invalid_tables: list[str] = field(default_factory=list)
    """존재하지 않는 테이블 목록"""

    invalid_columns: list[str] = field(default_factory=list)
    """존재하지 않는 컬럼 목록 (테이블.컬럼 형식)"""

    referenced_tables: list[str] = field(default_factory=list)
    """쿼리에서 참조하는 테이블 목록"""

    error_message: str | None = None
    """에러 메시지 (한국어)"""


# SQL 키워드 (테이블명으로 혼동하지 않도록)
SQL_KEYWORDS = frozenset(
    {
        "SELECT",
        "FROM",
        "WHERE",
        "AND",
        "OR",
        "NOT",
        "IN",
        "EXISTS",
        "BETWEEN",
        "LIKE",
        "IS",
        "NULL",
        "TRUE",
        "FALSE",
        "AS",
        "ON",
        "JOIN",
        "LEFT",
        "RIGHT",
        "INNER",
        "OUTER",
        "FULL",
        "CROSS",
        "GROUP",
        "BY",
        "ORDER",
        "HAVING",
        "LIMIT",
        "OFFSET",
        "UNION",
        "ALL",
        "DISTINCT",
        "CASE",
        "WHEN",
        "THEN",
        "ELSE",
        "END",
        "CAST",
        "COALESCE",
        "NULLIF",
        "WITH",
        "RECURSIVE",
        "ASC",
        "DESC",
        "OVER",
        "PARTITION",
        "ROW",
        "ROWS",
        "RANGE",
        "PRECEDING",
        "FOLLOWING",
        "UNBOUNDED",
        "CURRENT",
        "FIRST",
        "LAST",
        "FILTER",
        "WITHIN",
        "LATERAL",
        "NATURAL",
        "USING",
        "INTERVAL",
        "EXTRACT",
        "EPOCH",
        "NOW",
        "DATE",
        "TIME",
        "TIMESTAMP",
        "YEAR",
        "MONTH",
        "DAY",
        "HOUR",
        "MINUTE",
        "SECOND",
        "COUNT",
        "SUM",
        "AVG",
        "MAX",
        "MIN",
        "ARRAY",
        "ANY",
        "SOME",
        "BOOLEAN",
        "INTEGER",
        "BIGINT",
        "SMALLINT",
        "NUMERIC",
        "DECIMAL",
        "REAL",
        "FLOAT",
        "DOUBLE",
        "PRECISION",
        "VARCHAR",
        "CHAR",
        "TEXT",
        "SERIAL",
        "PRIMARY",
        "KEY",
        "FOREIGN",
        "REFERENCES",
        "UNIQUE",
        "CHECK",
        "DEFAULT",
        "CONSTRAINT",
    }
)

# 문자열 리터럴 패턴 (제거용)
STRING_LITERAL_PATTERN = re.compile(r"'[^']*'|\"[^\"]*\"")

# SQL 주석 패턴 (제거용)
COMMENT_PATTERN = re.compile(r"--.*?$|/\*.*?\*/", re.MULTILINE | re.DOTALL)


def _clean_query(query: str) -> str:
    """쿼리에서 문자열 리터럴과 주석 제거"""
    query = COMMENT_PATTERN.sub(" ", query)
    query = STRING_LITERAL_PATTERN.sub(" ", query)
    return query


def _extract_table_references(query: str) -> list[tuple[str, str | None]]:
    """
    쿼리에서 테이블 참조 추출

    Returns:
        list[tuple[str, str | None]]: (테이블명, 별칭) 튜플 리스트
    """
    cleaned = _clean_query(query)
    cleaned_upper = cleaned.upper()

    tables: list[tuple[str, str | None]] = []

    # FROM 절 패턴: FROM table_name [AS] alias
    from_pattern = re.compile(
        r"\bFROM\s+([a-zA-Z_][a-zA-Z0-9_]*)"
        r"(?:\s+(?:AS\s+)?([a-zA-Z_][a-zA-Z0-9_]*))?",
        re.IGNORECASE,
    )

    # JOIN 절 패턴: JOIN table_name [AS] alias
    join_pattern = re.compile(
        r"\bJOIN\s+([a-zA-Z_][a-zA-Z0-9_]*)"
        r"(?:\s+(?:AS\s+)?([a-zA-Z_][a-zA-Z0-9_]*))?",
        re.IGNORECASE,
    )

    # FROM 매칭
    for match in from_pattern.finditer(cleaned):
        table = match.group(1).lower()
        alias = match.group(2).lower() if match.group(2) else None

        # SQL 키워드 제외
        if table.upper() not in SQL_KEYWORDS:
            # 별칭이 SQL 키워드인 경우 무시
            if alias and alias.upper() in SQL_KEYWORDS:
                alias = None
            tables.append((table, alias))

    # JOIN 매칭
    for match in join_pattern.finditer(cleaned):
        table = match.group(1).lower()
        alias = match.group(2).lower() if match.group(2) else None

        # SQL 키워드 제외
        if table.upper() not in SQL_KEYWORDS:
            if alias and alias.upper() in SQL_KEYWORDS:
                alias = None
            tables.append((table, alias))

    return tables


def _extract_column_references(query: str) -> list[tuple[str | None, str]]:
    """
    쿼리에서 컬럼 참조 추출

    Returns:
        list[tuple[str | None, str]]: (테이블/별칭, 컬럼명) 튜플 리스트
    """
    cleaned = _clean_query(query)

    columns: list[tuple[str | None, str]] = []

    # SELECT 절 추출
    select_match = re.search(
        r"\bSELECT\s+(.*?)\s+FROM\b", cleaned, re.IGNORECASE | re.DOTALL
    )

    if not select_match:
        return columns

    select_clause = select_match.group(1)

    # SELECT * 체크
    if re.match(r"^\s*\*\s*$", select_clause) or re.match(
        r"^\s*DISTINCT\s+\*\s*$", select_clause, re.IGNORECASE
    ):
        return columns  # SELECT * 는 컬럼 검증 스킵

    # 컬럼 참조 패턴: [table.]column [AS alias]
    # 또는 함수(column) 형태
    column_pattern = re.compile(
        r"(?:([a-zA-Z_][a-zA-Z0-9_]*)\.)?([a-zA-Z_][a-zA-Z0-9_]*)"
        r"(?:\s+(?:AS\s+)?[a-zA-Z_][a-zA-Z0-9_]*)?",
        re.IGNORECASE,
    )

    for match in column_pattern.finditer(select_clause):
        table_or_alias = match.group(1).lower() if match.group(1) else None
        column = match.group(2).lower()

        # SQL 키워드와 함수 제외
        if column.upper() not in SQL_KEYWORDS:
            # 숫자로만 구성된 것 제외
            if not column.isdigit():
                columns.append((table_or_alias, column))

    return columns


def _build_schema_index(
    schema: DatabaseSchema,
) -> tuple[set[str], dict[str, set[str]]]:
    """
    스키마에서 테이블과 컬럼 인덱스 생성

    Returns:
        tuple[set[str], dict[str, set[str]]]: (테이블명 집합, 테이블별 컬럼 집합)
    """
    table_names: set[str] = set()
    table_columns: dict[str, set[str]] = {}

    for table in schema.tables:
        table_name = table.name.lower()
        table_names.add(table_name)
        table_columns[table_name] = {col.name.lower() for col in table.columns}

    return table_names, table_columns


def _generate_error_message(
    invalid_tables: list[str], invalid_columns: list[str]
) -> str:
    """한국어 에러 메시지 생성"""
    messages = []

    if invalid_tables:
        if len(invalid_tables) == 1:
            messages.append(f"테이블 '{invalid_tables[0]}'이(가) 존재하지 않습니다.")
        else:
            tables_str = ", ".join(f"'{t}'" for t in invalid_tables)
            messages.append(f"다음 테이블이 존재하지 않습니다: {tables_str}")

    if invalid_columns:
        if len(invalid_columns) == 1:
            messages.append(f"컬럼 '{invalid_columns[0]}'이(가) 존재하지 않습니다.")
        else:
            columns_str = ", ".join(f"'{c}'" for c in invalid_columns)
            messages.append(f"다음 컬럼이 존재하지 않습니다: {columns_str}")

    return " ".join(messages)


def validate_query_schema(query: str, schema: DatabaseSchema) -> SchemaValidationResult:
    """
    SQL 쿼리의 테이블/컬럼을 스키마와 대조하여 검증합니다 (2단계 검증).

    Args:
        query: 검증할 SQL 쿼리
        schema: 데이터베이스 스키마

    Returns:
        SchemaValidationResult: 검증 결과

    검증 규칙:
    1. 쿼리에서 참조하는 모든 테이블이 스키마에 존재해야 함
    2. 쿼리에서 참조하는 모든 컬럼이 해당 테이블에 존재해야 함
    """
    # 스키마 인덱스 생성
    valid_tables, table_columns = _build_schema_index(schema)

    # 테이블 참조 추출
    table_refs = _extract_table_references(query)

    # 별칭 매핑 생성
    alias_to_table: dict[str, str] = {}
    referenced_tables: list[str] = []
    invalid_tables: list[str] = []

    for table_name, alias in table_refs:
        if table_name not in valid_tables:
            if table_name not in invalid_tables:
                invalid_tables.append(table_name)
        else:
            if table_name not in referenced_tables:
                referenced_tables.append(table_name)
            if alias:
                alias_to_table[alias] = table_name

    # 테이블 검증 실패 시 조기 반환
    if invalid_tables:
        return SchemaValidationResult(
            is_valid=False,
            invalid_tables=invalid_tables,
            invalid_columns=[],
            referenced_tables=referenced_tables,
            error_message=_generate_error_message(invalid_tables, []),
        )

    # 컬럼 참조 추출 및 검증
    column_refs = _extract_column_references(query)
    invalid_columns: list[str] = []

    for table_or_alias, column in column_refs:
        # 테이블/별칭이 지정된 경우
        if table_or_alias:
            # 별칭을 테이블명으로 변환
            actual_table = alias_to_table.get(table_or_alias, table_or_alias)

            if actual_table in table_columns:
                if column not in table_columns[actual_table]:
                    col_ref = f"{actual_table}.{column}"
                    if col_ref not in invalid_columns:
                        invalid_columns.append(col_ref)
        else:
            # 테이블이 지정되지 않은 경우, 모든 참조 테이블에서 컬럼 검색
            found = False
            for table in referenced_tables:
                if table in table_columns and column in table_columns[table]:
                    found = True
                    break

            if not found and referenced_tables:
                # 컬럼을 찾지 못함
                if column not in invalid_columns:
                    invalid_columns.append(column)

    if invalid_columns:
        return SchemaValidationResult(
            is_valid=False,
            invalid_tables=[],
            invalid_columns=invalid_columns,
            referenced_tables=referenced_tables,
            error_message=_generate_error_message([], invalid_columns),
        )

    # 모든 검증 통과
    return SchemaValidationResult(
        is_valid=True,
        invalid_tables=[],
        invalid_columns=[],
        referenced_tables=referenced_tables,
        error_message=None,
    )
