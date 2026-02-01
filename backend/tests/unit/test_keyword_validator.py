"""
키워드 검증기 단위 테스트

모든 위험 키워드에 대한 검증 테스트입니다.
"""

import pytest

from app.validation.keyword_validator import (
    DANGEROUS_KEYWORDS,
    KeywordValidationResult,
    validate_query_keywords,
)


class TestDangerousKeywords:
    """위험 키워드 상수 테스트"""

    def test_dangerous_keywords_contains_update(self) -> None:
        """UPDATE 키워드가 포함되어 있어야 함"""
        assert "UPDATE" in DANGEROUS_KEYWORDS

    def test_dangerous_keywords_contains_delete(self) -> None:
        """DELETE 키워드가 포함되어 있어야 함"""
        assert "DELETE" in DANGEROUS_KEYWORDS

    def test_dangerous_keywords_contains_insert(self) -> None:
        """INSERT 키워드가 포함되어 있어야 함"""
        assert "INSERT" in DANGEROUS_KEYWORDS

    def test_dangerous_keywords_contains_drop(self) -> None:
        """DROP 키워드가 포함되어 있어야 함"""
        assert "DROP" in DANGEROUS_KEYWORDS

    def test_dangerous_keywords_contains_alter(self) -> None:
        """ALTER 키워드가 포함되어 있어야 함"""
        assert "ALTER" in DANGEROUS_KEYWORDS

    def test_dangerous_keywords_contains_truncate(self) -> None:
        """TRUNCATE 키워드가 포함되어 있어야 함"""
        assert "TRUNCATE" in DANGEROUS_KEYWORDS

    def test_dangerous_keywords_contains_grant(self) -> None:
        """GRANT 키워드가 포함되어 있어야 함"""
        assert "GRANT" in DANGEROUS_KEYWORDS

    def test_dangerous_keywords_contains_revoke(self) -> None:
        """REVOKE 키워드가 포함되어 있어야 함"""
        assert "REVOKE" in DANGEROUS_KEYWORDS

    def test_dangerous_keywords_contains_create(self) -> None:
        """CREATE 키워드가 포함되어 있어야 함"""
        assert "CREATE" in DANGEROUS_KEYWORDS

    def test_dangerous_keywords_contains_modify(self) -> None:
        """MODIFY 키워드가 포함되어 있어야 함"""
        assert "MODIFY" in DANGEROUS_KEYWORDS

    def test_dangerous_keywords_contains_exec(self) -> None:
        """EXEC 키워드가 포함되어 있어야 함"""
        assert "EXEC" in DANGEROUS_KEYWORDS

    def test_dangerous_keywords_contains_execute(self) -> None:
        """EXECUTE 키워드가 포함되어 있어야 함"""
        assert "EXECUTE" in DANGEROUS_KEYWORDS


class TestValidateQueryKeywords:
    """validate_query_keywords 함수 테스트"""

    # === 안전한 쿼리 테스트 ===

    def test_safe_select_query(self) -> None:
        """간단한 SELECT 쿼리는 통과"""
        query = "SELECT * FROM users"
        result = validate_query_keywords(query)

        assert result.is_valid is True
        assert result.detected_keywords == []
        assert result.error_message is None

    def test_safe_select_with_where(self) -> None:
        """WHERE 절이 있는 SELECT 쿼리는 통과"""
        query = "SELECT id, name FROM users WHERE status = 'active'"
        result = validate_query_keywords(query)

        assert result.is_valid is True

    def test_safe_select_with_join(self) -> None:
        """JOIN이 있는 SELECT 쿼리는 통과"""
        query = """
            SELECT u.name, o.total
            FROM users u
            JOIN orders o ON u.id = o.user_id
            WHERE o.created_at >= '2024-01-01'
        """
        result = validate_query_keywords(query)

        assert result.is_valid is True

    def test_safe_select_with_aggregation(self) -> None:
        """집계 함수가 있는 SELECT 쿼리는 통과"""
        query = """
            SELECT product_id, SUM(quantity) as total_quantity
            FROM order_items
            GROUP BY product_id
            HAVING SUM(quantity) > 100
        """
        result = validate_query_keywords(query)

        assert result.is_valid is True

    def test_safe_select_with_subquery(self) -> None:
        """서브쿼리가 있는 SELECT 쿼리는 통과"""
        query = """
            SELECT * FROM users
            WHERE id IN (SELECT user_id FROM orders WHERE total > 10000)
        """
        result = validate_query_keywords(query)

        assert result.is_valid is True

    def test_safe_select_with_cte(self) -> None:
        """WITH 절(CTE)이 있는 SELECT 쿼리는 통과"""
        query = """
            WITH recent_orders AS (
                SELECT * FROM orders WHERE created_at >= NOW() - INTERVAL '30 days'
            )
            SELECT * FROM recent_orders
        """
        result = validate_query_keywords(query)

        assert result.is_valid is True

    # === 위험 키워드 감지 테스트 ===

    def test_detect_update(self) -> None:
        """UPDATE 쿼리 감지"""
        query = "UPDATE users SET name = 'test' WHERE id = 1"
        result = validate_query_keywords(query)

        assert result.is_valid is False
        assert "UPDATE" in result.detected_keywords
        assert result.error_message is not None

    def test_detect_delete(self) -> None:
        """DELETE 쿼리 감지"""
        query = "DELETE FROM users WHERE id = 1"
        result = validate_query_keywords(query)

        assert result.is_valid is False
        assert "DELETE" in result.detected_keywords

    def test_detect_insert(self) -> None:
        """INSERT 쿼리 감지"""
        query = "INSERT INTO users (name, email) VALUES ('test', 'test@test.com')"
        result = validate_query_keywords(query)

        assert result.is_valid is False
        assert "INSERT" in result.detected_keywords

    def test_detect_drop_table(self) -> None:
        """DROP TABLE 쿼리 감지"""
        query = "DROP TABLE users"
        result = validate_query_keywords(query)

        assert result.is_valid is False
        assert "DROP" in result.detected_keywords

    def test_detect_drop_database(self) -> None:
        """DROP DATABASE 쿼리 감지"""
        query = "DROP DATABASE production"
        result = validate_query_keywords(query)

        assert result.is_valid is False
        assert "DROP" in result.detected_keywords

    def test_detect_alter_table(self) -> None:
        """ALTER TABLE 쿼리 감지"""
        query = "ALTER TABLE users ADD COLUMN age INTEGER"
        result = validate_query_keywords(query)

        assert result.is_valid is False
        assert "ALTER" in result.detected_keywords

    def test_detect_truncate(self) -> None:
        """TRUNCATE 쿼리 감지"""
        query = "TRUNCATE TABLE users"
        result = validate_query_keywords(query)

        assert result.is_valid is False
        assert "TRUNCATE" in result.detected_keywords

    def test_detect_grant(self) -> None:
        """GRANT 쿼리 감지"""
        query = "GRANT SELECT ON users TO public"
        result = validate_query_keywords(query)

        assert result.is_valid is False
        assert "GRANT" in result.detected_keywords

    def test_detect_revoke(self) -> None:
        """REVOKE 쿼리 감지"""
        query = "REVOKE SELECT ON users FROM public"
        result = validate_query_keywords(query)

        assert result.is_valid is False
        assert "REVOKE" in result.detected_keywords

    def test_detect_create_table(self) -> None:
        """CREATE TABLE 쿼리 감지"""
        query = "CREATE TABLE new_users (id SERIAL PRIMARY KEY, name VARCHAR(100))"
        result = validate_query_keywords(query)

        assert result.is_valid is False
        assert "CREATE" in result.detected_keywords

    def test_detect_exec(self) -> None:
        """EXEC 쿼리 감지"""
        query = "EXEC sp_delete_all_users"
        result = validate_query_keywords(query)

        assert result.is_valid is False
        assert "EXEC" in result.detected_keywords

    def test_detect_execute(self) -> None:
        """EXECUTE 쿼리 감지"""
        query = "EXECUTE delete_users_procedure"
        result = validate_query_keywords(query)

        assert result.is_valid is False
        assert "EXECUTE" in result.detected_keywords

    # === 대소문자 테스트 ===

    def test_detect_lowercase_delete(self) -> None:
        """소문자 DELETE 감지"""
        query = "delete from users where id = 1"
        result = validate_query_keywords(query)

        assert result.is_valid is False
        assert "DELETE" in result.detected_keywords

    def test_detect_mixed_case_update(self) -> None:
        """대소문자 혼합 UPDATE 감지"""
        query = "UpDaTe users SET name = 'test'"
        result = validate_query_keywords(query)

        assert result.is_valid is False
        assert "UPDATE" in result.detected_keywords

    # === 복합 쿼리 테스트 ===

    def test_detect_multiple_dangerous_keywords(self) -> None:
        """여러 위험 키워드 동시 감지"""
        query = "DROP TABLE users; DELETE FROM orders;"
        result = validate_query_keywords(query)

        assert result.is_valid is False
        assert "DROP" in result.detected_keywords
        assert "DELETE" in result.detected_keywords

    def test_detect_dangerous_in_subquery(self) -> None:
        """서브쿼리에 숨겨진 위험 쿼리 감지"""
        query = "SELECT * FROM (DELETE FROM users RETURNING *) AS deleted"
        result = validate_query_keywords(query)

        assert result.is_valid is False
        assert "DELETE" in result.detected_keywords

    # === 엣지 케이스 테스트 ===

    def test_false_positive_deleted_column(self) -> None:
        """deleted 컬럼명은 통과해야 함"""
        query = "SELECT deleted FROM audit_log"
        result = validate_query_keywords(query)

        # 'deleted'는 'DELETE' 키워드가 아님
        assert result.is_valid is True

    def test_false_positive_updated_at_column(self) -> None:
        """updated_at 컬럼명은 통과해야 함"""
        query = "SELECT updated_at FROM users"
        result = validate_query_keywords(query)

        # 'updated_at'은 'UPDATE' 키워드가 아님
        assert result.is_valid is True

    def test_false_positive_insert_in_string(self) -> None:
        """문자열 내 INSERT는 통과해야 함"""
        query = "SELECT * FROM logs WHERE message = 'INSERT operation completed'"
        result = validate_query_keywords(query)

        # 주석이나 문자열 내부의 키워드는 무시해야 함
        # (구현에 따라 이 테스트는 조정 필요)
        assert result.is_valid is True

    def test_non_select_without_dangerous_keyword(self) -> None:
        """SELECT로 시작하지 않는 쿼리 감지"""
        query = "EXPLAIN SELECT * FROM users"
        result = validate_query_keywords(query)

        # EXPLAIN은 위험 키워드가 아니지만, 시작 키워드 검증에서 실패
        assert result.is_valid is False

    def test_empty_query(self) -> None:
        """빈 쿼리 처리"""
        query = ""
        result = validate_query_keywords(query)

        assert result.is_valid is False
        assert result.error_message is not None

    def test_whitespace_only_query(self) -> None:
        """공백만 있는 쿼리 처리"""
        query = "   \n\t  "
        result = validate_query_keywords(query)

        assert result.is_valid is False
        assert result.error_message is not None

    # === SQL Injection 패턴 테스트 ===

    def test_detect_semicolon_injection(self) -> None:
        """세미콜론 인젝션 감지"""
        query = "SELECT * FROM users; DROP TABLE users; --"
        result = validate_query_keywords(query)

        assert result.is_valid is False
        assert "DROP" in result.detected_keywords

    def test_detect_union_with_delete(self) -> None:
        """UNION을 이용한 삭제 시도 감지"""
        query = "SELECT * FROM users UNION DELETE FROM orders"
        result = validate_query_keywords(query)

        assert result.is_valid is False
        assert "DELETE" in result.detected_keywords

    def test_comment_injection_with_delete(self) -> None:
        """주석과 함께 삭제 시도 감지"""
        query = "SELECT * FROM users -- comment\nDELETE FROM orders"
        result = validate_query_keywords(query)

        assert result.is_valid is False
        assert "DELETE" in result.detected_keywords


class TestKeywordValidationResult:
    """KeywordValidationResult 모델 테스트"""

    def test_result_has_is_valid_field(self) -> None:
        """is_valid 필드 존재 확인"""
        result = KeywordValidationResult(is_valid=True)
        assert hasattr(result, "is_valid")

    def test_result_has_detected_keywords_field(self) -> None:
        """detected_keywords 필드 존재 확인"""
        result = KeywordValidationResult(is_valid=False, detected_keywords=["DELETE"])
        assert hasattr(result, "detected_keywords")
        assert result.detected_keywords == ["DELETE"]

    def test_result_has_error_message_field(self) -> None:
        """error_message 필드 존재 확인"""
        result = KeywordValidationResult(
            is_valid=False, error_message="위험한 키워드가 감지되었습니다."
        )
        assert hasattr(result, "error_message")
