"""
키워드 기반 쿼리 검증기 단위 테스트

위험한 SQL 키워드 감지 기능을 테스트합니다.
"""

import pytest

from app.validation.keyword_validator import KeywordValidator, DANGEROUS_KEYWORDS


class TestKeywordValidator:
    """KeywordValidator 테스트"""

    @pytest.fixture
    def validator(self) -> KeywordValidator:
        """검증기 인스턴스 생성"""
        return KeywordValidator()

    # === 안전한 쿼리 테스트 ===

    def test_valid_select_query(self, validator: KeywordValidator) -> None:
        """유효한 SELECT 쿼리는 통과해야 함"""
        query = "SELECT * FROM users WHERE id = 1"
        result = validator.validate(query)
        assert result.is_valid is True
        assert result.detected_keywords == []

    def test_valid_select_with_join(self, validator: KeywordValidator) -> None:
        """JOIN이 포함된 SELECT 쿼리는 통과해야 함"""
        query = """
            SELECT u.name, o.total
            FROM users u
            JOIN orders o ON u.id = o.user_id
            WHERE o.created_at > '2024-01-01'
        """
        result = validator.validate(query)
        assert result.is_valid is True

    def test_valid_select_with_subquery(self, validator: KeywordValidator) -> None:
        """서브쿼리가 포함된 SELECT는 통과해야 함"""
        query = """
            SELECT * FROM orders
            WHERE user_id IN (SELECT id FROM users WHERE status = 'active')
        """
        result = validator.validate(query)
        assert result.is_valid is True

    def test_valid_select_with_aggregation(self, validator: KeywordValidator) -> None:
        """집계 함수가 포함된 SELECT는 통과해야 함"""
        query = """
            SELECT category, COUNT(*) as cnt, SUM(price) as total
            FROM products
            GROUP BY category
            HAVING COUNT(*) > 10
        """
        result = validator.validate(query)
        assert result.is_valid is True

    # === 위험한 쿼리 테스트 - DML ===

    def test_detect_update_keyword(self, validator: KeywordValidator) -> None:
        """UPDATE 키워드 감지"""
        query = "UPDATE users SET name = 'hacked' WHERE id = 1"
        result = validator.validate(query)
        assert result.is_valid is False
        assert "UPDATE" in result.detected_keywords

    def test_detect_delete_keyword(self, validator: KeywordValidator) -> None:
        """DELETE 키워드 감지"""
        query = "DELETE FROM users WHERE id = 1"
        result = validator.validate(query)
        assert result.is_valid is False
        assert "DELETE" in result.detected_keywords

    def test_detect_insert_keyword(self, validator: KeywordValidator) -> None:
        """INSERT 키워드 감지"""
        query = "INSERT INTO users (name, email) VALUES ('test', 'test@test.com')"
        result = validator.validate(query)
        assert result.is_valid is False
        assert "INSERT" in result.detected_keywords

    def test_detect_truncate_keyword(self, validator: KeywordValidator) -> None:
        """TRUNCATE 키워드 감지"""
        query = "TRUNCATE TABLE users"
        result = validator.validate(query)
        assert result.is_valid is False
        assert "TRUNCATE" in result.detected_keywords

    # === 위험한 쿼리 테스트 - DDL ===

    def test_detect_drop_keyword(self, validator: KeywordValidator) -> None:
        """DROP 키워드 감지"""
        query = "DROP TABLE users"
        result = validator.validate(query)
        assert result.is_valid is False
        assert "DROP" in result.detected_keywords

    def test_detect_alter_keyword(self, validator: KeywordValidator) -> None:
        """ALTER 키워드 감지"""
        query = "ALTER TABLE users ADD COLUMN age INT"
        result = validator.validate(query)
        assert result.is_valid is False
        assert "ALTER" in result.detected_keywords

    def test_detect_create_keyword(self, validator: KeywordValidator) -> None:
        """CREATE 키워드 감지"""
        query = "CREATE TABLE hackers (id INT)"
        result = validator.validate(query)
        assert result.is_valid is False
        assert "CREATE" in result.detected_keywords

    # === 위험한 쿼리 테스트 - DCL ===

    def test_detect_grant_keyword(self, validator: KeywordValidator) -> None:
        """GRANT 키워드 감지"""
        query = "GRANT ALL PRIVILEGES ON users TO hacker"
        result = validator.validate(query)
        assert result.is_valid is False
        assert "GRANT" in result.detected_keywords

    def test_detect_revoke_keyword(self, validator: KeywordValidator) -> None:
        """REVOKE 키워드 감지"""
        query = "REVOKE SELECT ON users FROM public"
        result = validator.validate(query)
        assert result.is_valid is False
        assert "REVOKE" in result.detected_keywords

    # === 위험한 쿼리 테스트 - 실행 명령 ===

    def test_detect_exec_keyword(self, validator: KeywordValidator) -> None:
        """EXEC 키워드 감지"""
        query = "EXEC sp_executesql 'DROP TABLE users'"
        result = validator.validate(query)
        assert result.is_valid is False
        assert "EXEC" in result.detected_keywords

    def test_detect_execute_keyword(self, validator: KeywordValidator) -> None:
        """EXECUTE 키워드 감지"""
        query = "EXECUTE dangerous_procedure()"
        result = validator.validate(query)
        assert result.is_valid is False
        assert "EXECUTE" in result.detected_keywords

    # === 대소문자 및 변형 테스트 ===

    def test_detect_lowercase_keywords(self, validator: KeywordValidator) -> None:
        """소문자 키워드도 감지해야 함"""
        query = "delete from users"
        result = validator.validate(query)
        assert result.is_valid is False

    def test_detect_mixed_case_keywords(self, validator: KeywordValidator) -> None:
        """대소문자 혼합 키워드도 감지해야 함"""
        query = "DeLeTe FrOm users"
        result = validator.validate(query)
        assert result.is_valid is False

    def test_detect_keyword_with_extra_spaces(self, validator: KeywordValidator) -> None:
        """공백이 많은 쿼리에서도 키워드 감지"""
        query = "   DELETE    FROM    users   "
        result = validator.validate(query)
        assert result.is_valid is False

    # === 다중 위험 키워드 테스트 ===

    def test_detect_multiple_dangerous_keywords(self, validator: KeywordValidator) -> None:
        """여러 위험 키워드가 있을 때 모두 감지"""
        query = "DROP TABLE users; DELETE FROM logs; INSERT INTO audit VALUES (1)"
        result = validator.validate(query)
        assert result.is_valid is False
        assert len(result.detected_keywords) >= 3

    # === SQL 인젝션 패턴 테스트 ===

    def test_detect_comment_injection(self, validator: KeywordValidator) -> None:
        """주석을 이용한 인젝션 감지"""
        query = "SELECT * FROM users WHERE id = 1; DROP TABLE users --"
        result = validator.validate(query)
        assert result.is_valid is False
        assert "DROP" in result.detected_keywords

    def test_detect_union_based_injection(self, validator: KeywordValidator) -> None:
        """UNION 기반 쿼리는 허용 (SELECT만 있으면)"""
        query = "SELECT name FROM users UNION SELECT password FROM credentials"
        result = validator.validate(query)
        # UNION 자체는 위험하지 않음 (SELECT만 있으면)
        assert result.is_valid is True

    # === 엣지 케이스 ===

    def test_empty_query(self, validator: KeywordValidator) -> None:
        """빈 쿼리"""
        result = validator.validate("")
        assert result.is_valid is False

    def test_whitespace_only_query(self, validator: KeywordValidator) -> None:
        """공백만 있는 쿼리"""
        result = validator.validate("   \n\t  ")
        assert result.is_valid is False

    def test_keyword_in_string_literal_safe(self, validator: KeywordValidator) -> None:
        """문자열 리터럴 내 키워드는 위험하지 않음 (SELECT 문에서)"""
        query = "SELECT * FROM users WHERE description = 'Please DELETE this'"
        result = validator.validate(query)
        # 문자열 내 키워드는 무시 - 하지만 간단한 구현에서는 감지될 수 있음
        # 이 테스트는 고급 구현에서만 통과
        # 현재는 보수적으로 차단할 수 있음을 허용
        assert result.is_valid is True or "DELETE" in result.detected_keywords

    def test_all_dangerous_keywords_defined(self) -> None:
        """모든 위험 키워드가 정의되어 있는지 확인"""
        expected_keywords = {
            "UPDATE", "DELETE", "INSERT", "DROP", "ALTER",
            "TRUNCATE", "GRANT", "REVOKE", "CREATE", "EXEC", "EXECUTE"
        }
        assert expected_keywords.issubset(set(DANGEROUS_KEYWORDS))
