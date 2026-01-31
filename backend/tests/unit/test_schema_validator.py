"""
스키마 검증기 단위 테스트

SQL 쿼리에서 참조하는 테이블/컬럼이 실제 스키마에 존재하는지 검증합니다.
"""

import pytest

from app.models.entities import DatabaseSchema, TableInfo, SchemaColumnInfo
from app.validation.schema_validator import SchemaValidator, ValidationResult


@pytest.fixture
def sample_schema() -> DatabaseSchema:
    """테스트용 샘플 스키마"""
    return DatabaseSchema(
        version="test-v1",
        tables=[
            TableInfo(
                name="users",
                description="사용자 테이블",
                columns=[
                    SchemaColumnInfo(name="id", data_type="integer", is_nullable=False, is_primary_key=True),
                    SchemaColumnInfo(name="name", data_type="varchar", is_nullable=False),
                    SchemaColumnInfo(name="email", data_type="varchar", is_nullable=False),
                    SchemaColumnInfo(name="created_at", data_type="timestamp", is_nullable=False),
                ],
                estimated_row_count=1000,
            ),
            TableInfo(
                name="orders",
                description="주문 테이블",
                columns=[
                    SchemaColumnInfo(name="id", data_type="integer", is_nullable=False, is_primary_key=True),
                    SchemaColumnInfo(name="user_id", data_type="integer", is_nullable=False),
                    SchemaColumnInfo(name="total_amount", data_type="decimal", is_nullable=False),
                    SchemaColumnInfo(name="status", data_type="varchar", is_nullable=False),
                    SchemaColumnInfo(name="created_at", data_type="timestamp", is_nullable=False),
                ],
                estimated_row_count=5000,
            ),
            TableInfo(
                name="products",
                description="상품 테이블",
                columns=[
                    SchemaColumnInfo(name="id", data_type="integer", is_nullable=False, is_primary_key=True),
                    SchemaColumnInfo(name="name", data_type="varchar", is_nullable=False),
                    SchemaColumnInfo(name="price", data_type="decimal", is_nullable=False),
                    SchemaColumnInfo(name="category", data_type="varchar", is_nullable=True),
                ],
                estimated_row_count=500,
            ),
        ],
    )


@pytest.fixture
def validator(sample_schema: DatabaseSchema) -> SchemaValidator:
    """검증기 인스턴스"""
    return SchemaValidator(sample_schema)


class TestSchemaValidator:
    """SchemaValidator 테스트"""

    # === 유효한 쿼리 테스트 ===

    def test_valid_simple_select(self, validator: SchemaValidator) -> None:
        """단순 SELECT 쿼리 검증"""
        query = "SELECT id, name, email FROM users"
        result = validator.validate(query)
        assert result.is_valid is True
        assert result.invalid_tables == []
        assert result.invalid_columns == []

    def test_valid_select_all_columns(self, validator: SchemaValidator) -> None:
        """SELECT * 쿼리 검증"""
        query = "SELECT * FROM users"
        result = validator.validate(query)
        assert result.is_valid is True

    def test_valid_select_with_alias(self, validator: SchemaValidator) -> None:
        """별칭이 있는 SELECT 쿼리 검증"""
        query = "SELECT u.id, u.name FROM users u WHERE u.id = 1"
        result = validator.validate(query)
        assert result.is_valid is True

    def test_valid_join_query(self, validator: SchemaValidator) -> None:
        """JOIN 쿼리 검증"""
        query = """
            SELECT u.name, o.total_amount
            FROM users u
            JOIN orders o ON u.id = o.user_id
            WHERE o.status = 'completed'
        """
        result = validator.validate(query)
        assert result.is_valid is True

    def test_valid_subquery(self, validator: SchemaValidator) -> None:
        """서브쿼리 검증"""
        query = """
            SELECT * FROM orders
            WHERE user_id IN (SELECT id FROM users WHERE name LIKE '%kim%')
        """
        result = validator.validate(query)
        assert result.is_valid is True

    def test_valid_aggregate_query(self, validator: SchemaValidator) -> None:
        """집계 쿼리 검증"""
        query = """
            SELECT user_id, COUNT(*) as order_count, SUM(total_amount) as total
            FROM orders
            GROUP BY user_id
            HAVING COUNT(*) > 5
        """
        result = validator.validate(query)
        assert result.is_valid is True

    def test_valid_multi_table_query(self, validator: SchemaValidator) -> None:
        """다중 테이블 쿼리 검증"""
        query = """
            SELECT u.name, o.id, p.name as product_name
            FROM users u, orders o, products p
            WHERE u.id = o.user_id
        """
        result = validator.validate(query)
        assert result.is_valid is True

    # === 존재하지 않는 테이블 테스트 ===

    def test_invalid_table(self, validator: SchemaValidator) -> None:
        """존재하지 않는 테이블 감지"""
        query = "SELECT * FROM nonexistent_table"
        result = validator.validate(query)
        assert result.is_valid is False
        assert "nonexistent_table" in result.invalid_tables

    def test_invalid_table_in_join(self, validator: SchemaValidator) -> None:
        """JOIN에서 존재하지 않는 테이블 감지"""
        query = """
            SELECT u.name
            FROM users u
            JOIN fake_table f ON u.id = f.user_id
        """
        result = validator.validate(query)
        assert result.is_valid is False
        assert "fake_table" in result.invalid_tables

    def test_invalid_table_in_subquery(self, validator: SchemaValidator) -> None:
        """서브쿼리에서 존재하지 않는 테이블 감지"""
        query = """
            SELECT * FROM users
            WHERE id IN (SELECT user_id FROM nonexistent)
        """
        result = validator.validate(query)
        assert result.is_valid is False
        assert "nonexistent" in result.invalid_tables

    # === 존재하지 않는 컬럼 테스트 ===

    def test_invalid_column(self, validator: SchemaValidator) -> None:
        """존재하지 않는 컬럼 감지"""
        query = "SELECT id, fake_column FROM users"
        result = validator.validate(query)
        assert result.is_valid is False
        assert "fake_column" in result.invalid_columns

    def test_invalid_column_in_where(self, validator: SchemaValidator) -> None:
        """WHERE 절에서 존재하지 않는 컬럼 감지"""
        query = "SELECT id FROM users WHERE nonexistent_col = 1"
        result = validator.validate(query)
        assert result.is_valid is False
        assert "nonexistent_col" in result.invalid_columns

    def test_invalid_column_with_valid_table(self, validator: SchemaValidator) -> None:
        """유효한 테이블의 존재하지 않는 컬럼 감지"""
        query = "SELECT users.fake_field FROM users"
        result = validator.validate(query)
        assert result.is_valid is False
        assert "fake_field" in result.invalid_columns

    # === 여러 오류 동시 감지 ===

    def test_multiple_invalid_tables(self, validator: SchemaValidator) -> None:
        """여러 존재하지 않는 테이블 감지"""
        query = "SELECT * FROM fake1 JOIN fake2 ON fake1.id = fake2.id"
        result = validator.validate(query)
        assert result.is_valid is False
        assert len(result.invalid_tables) >= 2

    def test_invalid_table_and_column(self, validator: SchemaValidator) -> None:
        """테이블과 컬럼 오류 동시 감지"""
        query = "SELECT fake_col FROM fake_table"
        result = validator.validate(query)
        assert result.is_valid is False
        # 테이블이 없으면 컬럼 검증도 실패할 수 있음

    # === 대소문자 처리 ===

    def test_case_insensitive_table_name(self, validator: SchemaValidator) -> None:
        """테이블명 대소문자 구분 안함"""
        query = "SELECT * FROM USERS"
        result = validator.validate(query)
        assert result.is_valid is True

    def test_case_insensitive_column_name(self, validator: SchemaValidator) -> None:
        """컬럼명 대소문자 구분 안함"""
        query = "SELECT ID, NAME FROM users"
        result = validator.validate(query)
        assert result.is_valid is True

    # === 엣지 케이스 ===

    def test_empty_query(self, validator: SchemaValidator) -> None:
        """빈 쿼리"""
        result = validator.validate("")
        assert result.is_valid is False

    def test_query_with_functions(self, validator: SchemaValidator) -> None:
        """함수가 포함된 쿼리"""
        query = "SELECT COUNT(*), MAX(id), MIN(created_at) FROM users"
        result = validator.validate(query)
        assert result.is_valid is True

    def test_query_with_literals(self, validator: SchemaValidator) -> None:
        """리터럴이 포함된 쿼리"""
        query = "SELECT id, 'constant' as label, 123 as num FROM users"
        result = validator.validate(query)
        assert result.is_valid is True


class TestSchemaValidatorHelpers:
    """SchemaValidator 헬퍼 메서드 테스트"""

    def test_get_all_table_names(self, validator: SchemaValidator) -> None:
        """모든 테이블명 반환"""
        tables = validator.get_all_table_names()
        assert "users" in tables
        assert "orders" in tables
        assert "products" in tables

    def test_get_columns_for_table(self, validator: SchemaValidator) -> None:
        """특정 테이블의 컬럼 목록 반환"""
        columns = validator.get_columns_for_table("users")
        assert "id" in columns
        assert "name" in columns
        assert "email" in columns
        assert "created_at" in columns

    def test_get_columns_for_nonexistent_table(self, validator: SchemaValidator) -> None:
        """존재하지 않는 테이블의 컬럼 요청"""
        columns = validator.get_columns_for_table("fake_table")
        assert columns == []

    def test_table_exists(self, validator: SchemaValidator) -> None:
        """테이블 존재 여부 확인"""
        assert validator.table_exists("users") is True
        assert validator.table_exists("fake") is False

    def test_column_exists(self, validator: SchemaValidator) -> None:
        """컬럼 존재 여부 확인"""
        assert validator.column_exists("users", "id") is True
        assert validator.column_exists("users", "fake") is False
        assert validator.column_exists("fake", "id") is False
