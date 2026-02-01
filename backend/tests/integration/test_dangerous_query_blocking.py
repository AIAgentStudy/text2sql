"""
위험 쿼리 차단 통합 테스트

3단계 검증 (키워드 → 스키마 → 시맨틱)을 통해 위험한 쿼리가 차단되는지 테스트합니다.
"""

import pytest

from app.errors.exceptions import DangerousQueryError, QueryValidationError
from app.models.entities import DatabaseSchema, SchemaColumnInfo, TableInfo
from app.validation.keyword_validator import validate_query_keywords
from app.validation.schema_validator import validate_query_schema


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
                        name="id", data_type="integer", is_nullable=False
                    ),
                    SchemaColumnInfo(
                        name="name", data_type="varchar", is_nullable=False
                    ),
                    SchemaColumnInfo(
                        name="email", data_type="varchar", is_nullable=True
                    ),
                ],
            ),
            TableInfo(
                name="orders",
                description="주문 정보",
                columns=[
                    SchemaColumnInfo(
                        name="id", data_type="integer", is_nullable=False
                    ),
                    SchemaColumnInfo(
                        name="user_id", data_type="integer", is_nullable=False
                    ),
                    SchemaColumnInfo(
                        name="total", data_type="numeric", is_nullable=False
                    ),
                    SchemaColumnInfo(
                        name="created_at", data_type="timestamp", is_nullable=False
                    ),
                ],
            ),
        ],
    )


class TestDangerousQueryBlocking:
    """위험 쿼리 차단 통합 테스트"""

    # === 데이터 삭제 시도 차단 테스트 ===

    def test_block_delete_all_users(self, sample_schema: DatabaseSchema) -> None:
        """'모든 사용자 삭제' 요청 차단"""
        # 이런 쿼리가 생성되면 차단되어야 함
        query = "DELETE FROM users"
        result = validate_query_keywords(query)

        assert result.is_valid is False
        assert "DELETE" in result.detected_keywords

    def test_block_delete_with_where(self, sample_schema: DatabaseSchema) -> None:
        """조건부 DELETE 쿼리 차단"""
        query = "DELETE FROM users WHERE id = 1"
        result = validate_query_keywords(query)

        assert result.is_valid is False

    def test_block_truncate_table(self, sample_schema: DatabaseSchema) -> None:
        """TRUNCATE 쿼리 차단"""
        query = "TRUNCATE TABLE users"
        result = validate_query_keywords(query)

        assert result.is_valid is False
        assert "TRUNCATE" in result.detected_keywords

    # === 데이터 수정 시도 차단 테스트 ===

    def test_block_update_users(self, sample_schema: DatabaseSchema) -> None:
        """UPDATE 쿼리 차단"""
        query = "UPDATE users SET name = 'hacked' WHERE id = 1"
        result = validate_query_keywords(query)

        assert result.is_valid is False
        assert "UPDATE" in result.detected_keywords

    def test_block_update_all_records(self, sample_schema: DatabaseSchema) -> None:
        """조건 없는 UPDATE 차단"""
        query = "UPDATE users SET email = 'test@test.com'"
        result = validate_query_keywords(query)

        assert result.is_valid is False

    # === 데이터 삽입 시도 차단 테스트 ===

    def test_block_insert_into_users(self, sample_schema: DatabaseSchema) -> None:
        """INSERT 쿼리 차단"""
        query = "INSERT INTO users (name, email) VALUES ('test', 'test@test.com')"
        result = validate_query_keywords(query)

        assert result.is_valid is False
        assert "INSERT" in result.detected_keywords

    def test_block_insert_select(self, sample_schema: DatabaseSchema) -> None:
        """INSERT ... SELECT 차단"""
        query = "INSERT INTO users (name, email) SELECT name, email FROM temp_users"
        result = validate_query_keywords(query)

        assert result.is_valid is False

    # === 스키마 변경 시도 차단 테스트 ===

    def test_block_drop_table(self, sample_schema: DatabaseSchema) -> None:
        """DROP TABLE 차단"""
        query = "DROP TABLE users"
        result = validate_query_keywords(query)

        assert result.is_valid is False
        assert "DROP" in result.detected_keywords

    def test_block_drop_database(self, sample_schema: DatabaseSchema) -> None:
        """DROP DATABASE 차단"""
        query = "DROP DATABASE production"
        result = validate_query_keywords(query)

        assert result.is_valid is False

    def test_block_alter_table(self, sample_schema: DatabaseSchema) -> None:
        """ALTER TABLE 차단"""
        query = "ALTER TABLE users ADD COLUMN password VARCHAR(255)"
        result = validate_query_keywords(query)

        assert result.is_valid is False
        assert "ALTER" in result.detected_keywords

    def test_block_create_table(self, sample_schema: DatabaseSchema) -> None:
        """CREATE TABLE 차단"""
        query = "CREATE TABLE evil_table (id SERIAL PRIMARY KEY)"
        result = validate_query_keywords(query)

        assert result.is_valid is False
        assert "CREATE" in result.detected_keywords

    # === 권한 변경 시도 차단 테스트 ===

    def test_block_grant(self, sample_schema: DatabaseSchema) -> None:
        """GRANT 차단"""
        query = "GRANT ALL PRIVILEGES ON users TO attacker"
        result = validate_query_keywords(query)

        assert result.is_valid is False
        assert "GRANT" in result.detected_keywords

    def test_block_revoke(self, sample_schema: DatabaseSchema) -> None:
        """REVOKE 차단"""
        query = "REVOKE ALL PRIVILEGES ON users FROM admin"
        result = validate_query_keywords(query)

        assert result.is_valid is False
        assert "REVOKE" in result.detected_keywords

    # === SQL Injection 패턴 차단 테스트 ===

    def test_block_semicolon_injection(self, sample_schema: DatabaseSchema) -> None:
        """세미콜론 인젝션 차단"""
        query = "SELECT * FROM users; DROP TABLE users;"
        result = validate_query_keywords(query)

        assert result.is_valid is False

    def test_block_comment_injection(self, sample_schema: DatabaseSchema) -> None:
        """주석 인젝션 차단"""
        query = "SELECT * FROM users -- comment\n; DELETE FROM orders"
        result = validate_query_keywords(query)

        assert result.is_valid is False

    def test_block_union_injection(self, sample_schema: DatabaseSchema) -> None:
        """UNION 인젝션 차단"""
        query = "SELECT name FROM users UNION DELETE FROM orders RETURNING *"
        result = validate_query_keywords(query)

        assert result.is_valid is False

    # === 다단계 검증 통합 테스트 ===

    def test_layered_validation_safe_query(self, sample_schema: DatabaseSchema) -> None:
        """안전한 쿼리는 모든 단계 통과"""
        query = "SELECT name, email FROM users WHERE id = 1"

        # 1단계: 키워드 검증
        keyword_result = validate_query_keywords(query)
        assert keyword_result.is_valid is True

        # 2단계: 스키마 검증
        schema_result = validate_query_schema(query, sample_schema)
        assert schema_result.is_valid is True

    def test_layered_validation_blocked_at_keyword(
        self, sample_schema: DatabaseSchema
    ) -> None:
        """위험 키워드는 1단계에서 차단"""
        query = "DELETE FROM users WHERE id = 1"

        # 1단계: 키워드 검증에서 차단
        keyword_result = validate_query_keywords(query)
        assert keyword_result.is_valid is False

        # 2단계로 진행하지 않음

    def test_layered_validation_blocked_at_schema(
        self, sample_schema: DatabaseSchema
    ) -> None:
        """존재하지 않는 테이블은 2단계에서 차단"""
        query = "SELECT * FROM customers"

        # 1단계: 키워드 검증 통과
        keyword_result = validate_query_keywords(query)
        assert keyword_result.is_valid is True

        # 2단계: 스키마 검증에서 차단
        schema_result = validate_query_schema(query, sample_schema)
        assert schema_result.is_valid is False
        assert "customers" in schema_result.invalid_tables

    # === 복합 공격 패턴 테스트 ===

    def test_block_complex_injection_1(self, sample_schema: DatabaseSchema) -> None:
        """복합 인젝션 패턴 1 차단"""
        query = """
            SELECT * FROM users WHERE name = '' OR 1=1;
            DROP TABLE users; --
        """
        result = validate_query_keywords(query)

        assert result.is_valid is False

    def test_block_complex_injection_2(self, sample_schema: DatabaseSchema) -> None:
        """복합 인젝션 패턴 2 차단"""
        query = """
            SELECT * FROM users WHERE id = 1
            UNION ALL SELECT * FROM (DELETE FROM orders RETURNING *) as x
        """
        result = validate_query_keywords(query)

        assert result.is_valid is False

    def test_block_complex_injection_3(self, sample_schema: DatabaseSchema) -> None:
        """복합 인젝션 패턴 3 차단"""
        query = """
            UPDATE users SET password = 'hacked'
            WHERE id IN (SELECT id FROM users WHERE role = 'admin')
        """
        result = validate_query_keywords(query)

        assert result.is_valid is False


class TestSafeQueryAllowed:
    """안전한 쿼리 허용 테스트"""

    def test_allow_simple_select(self, sample_schema: DatabaseSchema) -> None:
        """단순 SELECT 허용"""
        query = "SELECT * FROM users"

        keyword_result = validate_query_keywords(query)
        schema_result = validate_query_schema(query, sample_schema)

        assert keyword_result.is_valid is True
        assert schema_result.is_valid is True

    def test_allow_select_with_join(self, sample_schema: DatabaseSchema) -> None:
        """JOIN SELECT 허용"""
        query = """
            SELECT u.name, o.total
            FROM users u
            JOIN orders o ON u.id = o.user_id
        """

        keyword_result = validate_query_keywords(query)
        schema_result = validate_query_schema(query, sample_schema)

        assert keyword_result.is_valid is True
        assert schema_result.is_valid is True

    def test_allow_select_with_aggregation(self, sample_schema: DatabaseSchema) -> None:
        """집계 SELECT 허용"""
        query = """
            SELECT user_id, SUM(total) as total_amount
            FROM orders
            GROUP BY user_id
            HAVING SUM(total) > 10000
        """

        keyword_result = validate_query_keywords(query)
        schema_result = validate_query_schema(query, sample_schema)

        assert keyword_result.is_valid is True
        assert schema_result.is_valid is True

    def test_allow_select_with_subquery(self, sample_schema: DatabaseSchema) -> None:
        """서브쿼리 SELECT 허용"""
        query = """
            SELECT * FROM users
            WHERE id IN (SELECT user_id FROM orders WHERE total > 10000)
        """

        keyword_result = validate_query_keywords(query)
        schema_result = validate_query_schema(query, sample_schema)

        assert keyword_result.is_valid is True
        assert schema_result.is_valid is True

    def test_allow_complex_analytical_query(
        self, sample_schema: DatabaseSchema
    ) -> None:
        """복잡한 분석 쿼리 허용"""
        query = """
            WITH user_totals AS (
                SELECT user_id, SUM(total) as total_amount
                FROM orders
                GROUP BY user_id
            )
            SELECT u.name, ut.total_amount
            FROM users u
            JOIN user_totals ut ON u.id = ut.user_id
            ORDER BY ut.total_amount DESC
            LIMIT 10
        """

        keyword_result = validate_query_keywords(query)
        schema_result = validate_query_schema(query, sample_schema)

        assert keyword_result.is_valid is True
        assert schema_result.is_valid is True


class TestErrorMessages:
    """에러 메시지 테스트"""

    def test_delete_error_message_korean(self) -> None:
        """DELETE 차단 시 한국어 메시지"""
        query = "DELETE FROM users"
        result = validate_query_keywords(query)

        assert result.is_valid is False
        assert result.error_message is not None
        # 한국어 메시지 확인
        assert "데이터" in result.error_message or "삭제" in result.error_message or "조회" in result.error_message

    def test_update_error_message_korean(self) -> None:
        """UPDATE 차단 시 한국어 메시지"""
        query = "UPDATE users SET name = 'test'"
        result = validate_query_keywords(query)

        assert result.is_valid is False
        assert result.error_message is not None

    def test_invalid_table_error_message(self, sample_schema: DatabaseSchema) -> None:
        """존재하지 않는 테이블 에러 메시지"""
        query = "SELECT * FROM customers"
        result = validate_query_schema(query, sample_schema)

        assert result.is_valid is False
        assert result.error_message is not None
        assert "customers" in result.error_message
