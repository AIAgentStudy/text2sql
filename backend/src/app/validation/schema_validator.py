"""
스키마 기반 SQL 쿼리 검증기

2단계 검증: 쿼리에서 참조하는 테이블과 컬럼이 실제 스키마에 존재하는지 확인합니다.
"""

import re
from dataclasses import dataclass, field

from app.models.entities import DatabaseSchema


@dataclass
class ValidationResult:
    """스키마 검증 결과"""

    is_valid: bool
    """검증 통과 여부"""

    invalid_tables: list[str] = field(default_factory=list)
    """존재하지 않는 테이블 목록"""

    invalid_columns: list[str] = field(default_factory=list)
    """존재하지 않는 컬럼 목록"""

    error_message: str = ""
    """사용자에게 표시할 에러 메시지"""


class SchemaValidator:
    """
    스키마 기반 SQL 쿼리 검증기

    실제 데이터베이스 스키마와 비교하여 쿼리에서 참조하는
    테이블과 컬럼이 존재하는지 검증합니다.
    """

    def __init__(self, schema: DatabaseSchema) -> None:
        """
        검증기 초기화

        Args:
            schema: 데이터베이스 스키마 정보
        """
        self._schema = schema

        # 빠른 조회를 위한 인덱스 구축
        self._tables: dict[str, set[str]] = {}
        for table in schema.tables:
            table_name_lower = table.name.lower()
            self._tables[table_name_lower] = {
                col.name.lower() for col in table.columns
            }

    def validate(self, query: str) -> ValidationResult:
        """
        SQL 쿼리의 스키마 유효성 검증

        Args:
            query: 검증할 SQL 쿼리

        Returns:
            ValidationResult: 검증 결과
        """
        if not query or not query.strip():
            return ValidationResult(
                is_valid=False,
                error_message="쿼리가 비어있습니다.",
            )

        # 쿼리 정규화
        normalized_query = self._normalize_query(query)

        # 테이블 추출 및 검증
        referenced_tables = self._extract_tables(normalized_query)
        invalid_tables = [
            table for table in referenced_tables
            if not self.table_exists(table)
        ]

        # 컬럼 추출 및 검증 (테이블이 모두 유효한 경우에만)
        invalid_columns: list[str] = []
        if not invalid_tables:
            referenced_columns = self._extract_columns(normalized_query, referenced_tables)
            invalid_columns = self._validate_columns(referenced_columns, referenced_tables)

        # 결과 생성
        if invalid_tables or invalid_columns:
            error_message = self._generate_error_message(invalid_tables, invalid_columns)
            return ValidationResult(
                is_valid=False,
                invalid_tables=invalid_tables,
                invalid_columns=invalid_columns,
                error_message=error_message,
            )

        return ValidationResult(
            is_valid=True,
            invalid_tables=[],
            invalid_columns=[],
            error_message="",
        )

    def _normalize_query(self, query: str) -> str:
        """쿼리 정규화 (소문자 변환, 주석 제거)"""
        # 주석 제거
        query = re.sub(r"--[^\n]*", "", query)
        query = re.sub(r"/\*[\s\S]*?\*/", "", query)
        # 연속 공백 정리
        query = re.sub(r"\s+", " ", query)
        return query.strip().lower()

    def _extract_tables(self, query: str) -> list[str]:
        """
        쿼리에서 테이블 이름 추출

        FROM, JOIN, INTO, UPDATE, TABLE 등의 키워드 뒤에 오는 테이블명을 추출합니다.
        """
        tables: set[str] = set()

        # FROM 절 테이블
        from_pattern = r"\bfrom\s+([a-z_][a-z0-9_]*)"
        tables.update(re.findall(from_pattern, query))

        # JOIN 절 테이블
        join_pattern = r"\bjoin\s+([a-z_][a-z0-9_]*)"
        tables.update(re.findall(join_pattern, query))

        # 콤마로 구분된 테이블 (FROM a, b, c 형태)
        # FROM 뒤의 테이블 목록 처리
        comma_from_pattern = r"\bfrom\s+((?:[a-z_][a-z0-9_]*\s*,\s*)*[a-z_][a-z0-9_]*)"
        for match in re.findall(comma_from_pattern, query):
            for table in match.split(","):
                table = table.strip().split()[0]  # 별칭 제거
                if table:
                    tables.add(table)

        # 서브쿼리 내 테이블도 재귀적으로 처리
        # 간단한 구현에서는 위 패턴으로 대부분 커버됨

        return list(tables)

    def _extract_columns(
        self,
        query: str,
        referenced_tables: list[str],
    ) -> list[tuple[str | None, str]]:
        """
        쿼리에서 컬럼 참조 추출

        Returns:
            (테이블명 또는 None, 컬럼명) 튜플 목록
        """
        columns: list[tuple[str | None, str]] = []

        # 테이블.컬럼 형태
        qualified_pattern = r"\b([a-z_][a-z0-9_]*)\.([a-z_][a-z0-9_]*)\b"
        for match in re.findall(qualified_pattern, query):
            table_or_alias, column = match
            # 별칭을 실제 테이블로 매핑 (간단한 구현에서는 생략)
            columns.append((table_or_alias, column))

        # SELECT 절의 컬럼 (테이블 한정자 없는 경우)
        select_pattern = r"\bselect\s+(.*?)\s*\bfrom\b"
        select_match = re.search(select_pattern, query, re.DOTALL)
        if select_match:
            select_clause = select_match.group(1)
            # * 제외
            if select_clause.strip() != "*":
                # 각 컬럼 파싱
                for col_expr in select_clause.split(","):
                    col_expr = col_expr.strip()
                    # 함수나 별칭 처리
                    col_expr = re.sub(r"\s+as\s+[a-z_][a-z0-9_]*$", "", col_expr)
                    # 테이블.컬럼이 아닌 단순 컬럼명
                    if "." not in col_expr and col_expr.isidentifier():
                        columns.append((None, col_expr))

        # WHERE 절의 컬럼
        where_pattern = r"\bwhere\s+(.*?)(?:\bgroup\b|\border\b|\blimit\b|$)"
        where_match = re.search(where_pattern, query, re.DOTALL)
        if where_match:
            where_clause = where_match.group(1)
            # 단순 식별자 추출 (테이블 한정자 없는 경우)
            identifiers = re.findall(r"\b([a-z_][a-z0-9_]*)\s*[=<>!]", where_clause)
            for ident in identifiers:
                if ident not in ("and", "or", "not", "in", "is", "null", "like"):
                    columns.append((None, ident))

        return columns

    def _validate_columns(
        self,
        columns: list[tuple[str | None, str]],
        referenced_tables: list[str],
    ) -> list[str]:
        """
        컬럼 유효성 검증

        Args:
            columns: (테이블명 또는 None, 컬럼명) 튜플 목록
            referenced_tables: 쿼리에서 참조하는 테이블 목록

        Returns:
            유효하지 않은 컬럼 목록
        """
        invalid: list[str] = []

        for table_ref, column in columns:
            column_lower = column.lower()

            if table_ref:
                # 테이블이 지정된 경우
                table_lower = table_ref.lower()
                # 별칭일 수 있으므로 참조된 모든 테이블에서 확인
                if table_lower in self._tables:
                    if column_lower not in self._tables[table_lower]:
                        invalid.append(column)
                # 별칭인 경우는 통과 (정확한 검증은 복잡함)
            else:
                # 테이블이 지정되지 않은 경우
                # 참조된 테이블 중 하나에 존재하면 통과
                found = False
                for table in referenced_tables:
                    table_lower = table.lower()
                    if table_lower in self._tables:
                        if column_lower in self._tables[table_lower]:
                            found = True
                            break
                if not found:
                    # 집계 함수나 리터럴일 수 있으므로 확실한 경우만 추가
                    # 여기서는 보수적으로 처리
                    if column_lower not in self._get_all_columns():
                        invalid.append(column)

        return list(set(invalid))

    def _get_all_columns(self) -> set[str]:
        """모든 테이블의 모든 컬럼 반환"""
        all_cols: set[str] = set()
        for columns in self._tables.values():
            all_cols.update(columns)
        return all_cols

    def _generate_error_message(
        self,
        invalid_tables: list[str],
        invalid_columns: list[str],
    ) -> str:
        """에러 메시지 생성"""
        messages = []

        if invalid_tables:
            tables_str = ", ".join(f"'{t}'" for t in invalid_tables)
            messages.append(f"테이블을 찾을 수 없습니다: {tables_str}")

        if invalid_columns:
            columns_str = ", ".join(f"'{c}'" for c in invalid_columns)
            messages.append(f"컬럼을 찾을 수 없습니다: {columns_str}")

        return " / ".join(messages)

    # === 헬퍼 메서드 ===

    def get_all_table_names(self) -> list[str]:
        """모든 테이블명 반환"""
        return [table.name for table in self._schema.tables]

    def get_columns_for_table(self, table_name: str) -> list[str]:
        """특정 테이블의 컬럼 목록 반환"""
        table_lower = table_name.lower()
        if table_lower in self._tables:
            return list(self._tables[table_lower])
        return []

    def table_exists(self, table_name: str) -> bool:
        """테이블 존재 여부 확인"""
        return table_name.lower() in self._tables

    def column_exists(self, table_name: str, column_name: str) -> bool:
        """특정 테이블에 컬럼 존재 여부 확인"""
        table_lower = table_name.lower()
        if table_lower not in self._tables:
            return False
        return column_name.lower() in self._tables[table_lower]
