"""
스키마 검증기 단위 테스트

쿼리에서 사용하는 테이블/컬럼이 스키마에 존재하는지 검증합니다.
"""

import pytest

from app.models.entities import DatabaseSchema, SchemaColumnInfo, TableInfo
from app.validation.schema_validator import (
    SchemaValidationResult,
    validate_query_schema,
)


@pytest.fixture
def sample_schema() -> DatabaseSchema:
    """테스트용 샘플 스키마"""
    return DatabaseSchema(
        version="test123",
        tables=[
            TableInfo(
                name="users",
                description="사용자 정보",
                columns=[
                    SchemaColumnInfo(
                        name="id",
                        data_type="integer",
                        is_nullable=False,
                        is_primary_key=True,
                    ),
                    SchemaColumnInfo(
                        name="name",
                        data_type="varchar",
                        is_nullable=False,
                    ),
                    SchemaColumnInfo(
                        name="email",
                        data_type="varchar",
                        is_nullable=True,
                    ),
                    SchemaColumnInfo(
                        name="created_at",
                        data_type="timestamp",
                        is_nullable=False,
                    ),
                ],
            ),
            TableInfo(
                name="orders",
                description="주문 정보",
                columns=[
                    SchemaColumnInfo(
                        name="id",
                        data_type="integer",
                        is_nullable=False,
                        is_primary_key=True,
                    ),
                    SchemaColumnInfo(
                        name="user_id",
                        data_type="integer",
                        is_nullable=False,
                    ),
                    SchemaColumnInfo(
                        name="total",
                        data_type="numeric",
                        is_nullable=False,
                    ),
                    SchemaColumnInfo(
                        name="created_at",
                        data_type="timestamp",
                        is_nullable=False,
                    ),
                ],
            ),
            TableInfo(
                name="order_items",
                description="주문 항목",
                columns=[
                    SchemaColumnInfo(
                        name="id",
                        data_type="integer",
                        is_nullable=False,
                        is_primary_key=True,
                    ),
                    SchemaColumnInfo(
                        name="order_id",
                        data_type="integer",
                        is_nullable=False,
                    ),
                    SchemaColumnInfo(
                        name="product_id",
                        data_type="integer",
                        is_nullable=False,
                    ),
                    SchemaColumnInfo(
                        name="quantity",
                        data_type="integer",
                        is_nullable=False,
                    ),
                    SchemaColumnInfo(
                        name="price",
                        data_type="numeric",
                        is_nullable=False,
                    ),
                ],
            ),
            TableInfo(
                name="products",
                description="상품 정보",
                columns=[
                    SchemaColumnInfo(
                        name="id",
                        data_type="integer",
                        is_nullable=False,
                        is_primary_key=True,
                    ),
                    SchemaColumnInfo(
                        name="name",
                        data_type="varchar",
                        is_nullable=False,
                    ),
                    SchemaColumnInfo(
                        name="category",
                        data_type="varchar",
                        is_nullable=True,
                    ),
                    SchemaColumnInfo(
                        name="price",
                        data_type="numeric",
                        is_nullable=False,
                    ),
                ],
            ),
        ],
    )


class TestValidateQuerySchema:
    """validate_query_schema 함수 테스트"""

    # === 유효한 쿼리 테스트 ===

    def test_valid_simple_select(self, sample_schema: DatabaseSchema) -> None:
        """간단한 SELECT 쿼리 검증 통과"""
        query = "SELECT * FROM users"
        result = validate_query_schema(query, sample_schema)

        assert result.is_valid is True
        assert result.invalid_tables == []
        assert result.invalid_columns == []

    def test_valid_select_with_specific_columns(
        self, sample_schema: DatabaseSchema
    ) -> None:
        """특정 컬럼을 지정한 SELECT 쿼리 검증 통과"""
        query = "SELECT id, name, email FROM users"
        result = validate_query_schema(query, sample_schema)

        assert result.is_valid is True

    def test_valid_select_with_where(self, sample_schema: DatabaseSchema) -> None:
        """WHERE 절이 있는 SELECT 쿼리 검증 통과"""
        query = "SELECT * FROM users WHERE id = 1 AND name = 'test'"
        result = validate_query_schema(query, sample_schema)

        assert result.is_valid is True

    def test_valid_select_with_join(self, sample_schema: DatabaseSchema) -> None:
        """JOIN이 있는 SELECT 쿼리 검증 통과"""
        query = """
            SELECT u.name, o.total
            FROM users u
            JOIN orders o ON u.id = o.user_id
        """
        result = validate_query_schema(query, sample_schema)

        assert result.is_valid is True

    def test_valid_select_with_multiple_joins(
        self, sample_schema: DatabaseSchema
    ) -> None:
        """여러 JOIN이 있는 SELECT 쿼리 검증 통과"""
        query = """
            SELECT u.name, o.total, oi.quantity, p.name as product_name
            FROM users u
            JOIN orders o ON u.id = o.user_id
            JOIN order_items oi ON o.id = oi.order_id
            JOIN products p ON oi.product_id = p.id
        """
        result = validate_query_schema(query, sample_schema)

        assert result.is_valid is True

    def test_valid_select_with_aggregation(
        self, sample_schema: DatabaseSchema
    ) -> None:
        """집계 함수가 있는 SELECT 쿼리 검증 통과"""
        query = """
            SELECT user_id, SUM(total) as total_amount
            FROM orders
            GROUP BY user_id
        """
        result = validate_query_schema(query, sample_schema)

        assert result.is_valid is True

    def test_valid_select_with_alias(self, sample_schema: DatabaseSchema) -> None:
        """별칭이 있는 SELECT 쿼리 검증 통과"""
        query = "SELECT u.id, u.name AS user_name FROM users AS u"
        result = validate_query_schema(query, sample_schema)

        assert result.is_valid is True

    # === 테이블 검증 실패 테스트 ===

    def test_invalid_table_not_found(self, sample_schema: DatabaseSchema) -> None:
        """존재하지 않는 테이블 감지"""
        query = "SELECT * FROM customers"
        result = validate_query_schema(query, sample_schema)

        assert result.is_valid is False
        assert "customers" in result.invalid_tables

    def test_invalid_multiple_tables_not_found(
        self, sample_schema: DatabaseSchema
    ) -> None:
        """여러 존재하지 않는 테이블 감지"""
        query = "SELECT * FROM customers c JOIN vendors v ON c.id = v.customer_id"
        result = validate_query_schema(query, sample_schema)

        assert result.is_valid is False
        assert "customers" in result.invalid_tables
        assert "vendors" in result.invalid_tables

    def test_invalid_table_in_join(self, sample_schema: DatabaseSchema) -> None:
        """JOIN에서 존재하지 않는 테이블 감지"""
        query = """
            SELECT u.name, c.name
            FROM users u
            JOIN categories c ON u.id = c.user_id
        """
        result = validate_query_schema(query, sample_schema)

        assert result.is_valid is False
        assert "categories" in result.invalid_tables

    # === 컬럼 검증 실패 테스트 ===

    def test_invalid_column_not_found(self, sample_schema: DatabaseSchema) -> None:
        """존재하지 않는 컬럼 감지"""
        query = "SELECT id, username FROM users"
        result = validate_query_schema(query, sample_schema)

        assert result.is_valid is False
        assert any("username" in col for col in result.invalid_columns)

    def test_invalid_column_in_where(self, sample_schema: DatabaseSchema) -> None:
        """WHERE 절에서 존재하지 않는 컬럼 감지"""
        query = "SELECT * FROM users WHERE status = 'active'"
        result = validate_query_schema(query, sample_schema)

        assert result.is_valid is False
        assert any("status" in col for col in result.invalid_columns)

    def test_invalid_column_with_table_prefix(
        self, sample_schema: DatabaseSchema
    ) -> None:
        """테이블 접두사가 있는 존재하지 않는 컬럼 감지"""
        query = "SELECT u.id, u.phone FROM users u"
        result = validate_query_schema(query, sample_schema)

        assert result.is_valid is False
        assert any("phone" in col for col in result.invalid_columns)

    def test_invalid_column_in_join_condition(
        self, sample_schema: DatabaseSchema
    ) -> None:
        """JOIN 조건에서 존재하지 않는 컬럼 감지"""
        query = """
            SELECT u.name, o.total
            FROM users u
            JOIN orders o ON u.customer_id = o.user_id
        """
        result = validate_query_schema(query, sample_schema)

        assert result.is_valid is False
        assert any("customer_id" in col for col in result.invalid_columns)

    # === 엣지 케이스 테스트 ===

    def test_case_insensitive_table_name(self, sample_schema: DatabaseSchema) -> None:
        """테이블명 대소문자 무시"""
        query = "SELECT * FROM USERS"
        result = validate_query_schema(query, sample_schema)

        # PostgreSQL은 기본적으로 소문자로 변환
        assert result.is_valid is True

    def test_case_insensitive_column_name(self, sample_schema: DatabaseSchema) -> None:
        """컬럼명 대소문자 무시"""
        query = "SELECT ID, NAME FROM users"
        result = validate_query_schema(query, sample_schema)

        assert result.is_valid is True

    def test_select_star_bypass_column_check(
        self, sample_schema: DatabaseSchema
    ) -> None:
        """SELECT * 은 컬럼 검증 스킵"""
        query = "SELECT * FROM users"
        result = validate_query_schema(query, sample_schema)

        assert result.is_valid is True
        assert result.invalid_columns == []

    def test_valid_with_sql_functions(self, sample_schema: DatabaseSchema) -> None:
        """SQL 함수 사용 시 검증"""
        query = """
            SELECT COUNT(*), MAX(total), MIN(total), AVG(total)
            FROM orders
        """
        result = validate_query_schema(query, sample_schema)

        assert result.is_valid is True

    def test_valid_with_cast(self, sample_schema: DatabaseSchema) -> None:
        """CAST 사용 시 검증"""
        query = "SELECT CAST(total AS INTEGER) FROM orders"
        result = validate_query_schema(query, sample_schema)

        assert result.is_valid is True

    def test_valid_subquery(self, sample_schema: DatabaseSchema) -> None:
        """서브쿼리 검증"""
        query = """
            SELECT * FROM users
            WHERE id IN (SELECT user_id FROM orders WHERE total > 10000)
        """
        result = validate_query_schema(query, sample_schema)

        assert result.is_valid is True

    def test_invalid_subquery_table(self, sample_schema: DatabaseSchema) -> None:
        """서브쿼리에서 존재하지 않는 테이블 감지"""
        query = """
            SELECT * FROM users
            WHERE id IN (SELECT customer_id FROM invoices)
        """
        result = validate_query_schema(query, sample_schema)

        assert result.is_valid is False
        assert "invoices" in result.invalid_tables

    def test_empty_schema(self) -> None:
        """빈 스키마 처리"""
        empty_schema = DatabaseSchema(version="empty", tables=[])
        query = "SELECT * FROM users"
        result = validate_query_schema(query, empty_schema)

        assert result.is_valid is False
        assert "users" in result.invalid_tables


class TestSchemaValidationResult:
    """SchemaValidationResult 모델 테스트"""

    def test_result_has_is_valid_field(self) -> None:
        """is_valid 필드 존재 확인"""
        result = SchemaValidationResult(is_valid=True)
        assert hasattr(result, "is_valid")

    def test_result_has_invalid_tables_field(self) -> None:
        """invalid_tables 필드 존재 확인"""
        result = SchemaValidationResult(
            is_valid=False, invalid_tables=["customers", "vendors"]
        )
        assert hasattr(result, "invalid_tables")
        assert result.invalid_tables == ["customers", "vendors"]

    def test_result_has_invalid_columns_field(self) -> None:
        """invalid_columns 필드 존재 확인"""
        result = SchemaValidationResult(
            is_valid=False, invalid_columns=["users.phone", "orders.status"]
        )
        assert hasattr(result, "invalid_columns")
        assert result.invalid_columns == ["users.phone", "orders.status"]

    def test_result_has_error_message_field(self) -> None:
        """error_message 필드 존재 확인"""
        result = SchemaValidationResult(
            is_valid=False, error_message="테이블 'customers'가 존재하지 않습니다."
        )
        assert hasattr(result, "error_message")

    def test_result_has_referenced_tables_field(self) -> None:
        """referenced_tables 필드 존재 확인"""
        result = SchemaValidationResult(
            is_valid=True, referenced_tables=["users", "orders"]
        )
        assert hasattr(result, "referenced_tables")
        assert result.referenced_tables == ["users", "orders"]
