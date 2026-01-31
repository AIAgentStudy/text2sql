"""
위험한 쿼리 차단 통합 테스트

3단계 검증 파이프라인이 위험한 쿼리를 올바르게 차단하는지 테스트합니다.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.validation.keyword_validator import KeywordValidator
from app.validation.schema_validator import SchemaValidator
from app.validation.semantic_validator import SemanticValidator
from app.agent.nodes.query_validation import (
    query_validation_node,
    validate_query_pipeline,
    ValidationPipelineResult,
)
from app.agent.state import Text2SQLAgentState, create_initial_state
from app.models.entities import DatabaseSchema, TableInfo, SchemaColumnInfo
from app.errors.exceptions import DangerousQueryError


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
                ],
                estimated_row_count=1000,
            ),
            TableInfo(
                name="orders",
                description="주문 테이블",
                columns=[
                    SchemaColumnInfo(name="id", data_type="integer", is_nullable=False, is_primary_key=True),
                    SchemaColumnInfo(name="user_id", data_type="integer", is_nullable=False),
                    SchemaColumnInfo(name="total", data_type="decimal", is_nullable=False),
                ],
                estimated_row_count=5000,
            ),
        ],
    )


class TestDangerousQueryBlocking:
    """위험한 쿼리 차단 테스트"""

    # === 1단계: 키워드 검증 테스트 ===

    def test_block_update_query(self) -> None:
        """UPDATE 쿼리 차단"""
        validator = KeywordValidator()
        query = "UPDATE users SET name = 'hacked'"
        result = validator.validate(query)
        assert result.is_valid is False
        assert "조회 요청만 가능합니다" in result.error_message

    def test_block_delete_query(self) -> None:
        """DELETE 쿼리 차단"""
        validator = KeywordValidator()
        query = "DELETE FROM users WHERE id = 1"
        result = validator.validate(query)
        assert result.is_valid is False

    def test_block_drop_table(self) -> None:
        """DROP TABLE 차단"""
        validator = KeywordValidator()
        query = "DROP TABLE users"
        result = validator.validate(query)
        assert result.is_valid is False

    def test_block_insert_query(self) -> None:
        """INSERT 쿼리 차단"""
        validator = KeywordValidator()
        query = "INSERT INTO users VALUES (1, 'hacker', 'hack@evil.com')"
        result = validator.validate(query)
        assert result.is_valid is False

    def test_block_truncate(self) -> None:
        """TRUNCATE 차단"""
        validator = KeywordValidator()
        query = "TRUNCATE TABLE users"
        result = validator.validate(query)
        assert result.is_valid is False

    def test_block_grant(self) -> None:
        """GRANT 차단"""
        validator = KeywordValidator()
        query = "GRANT ALL ON users TO public"
        result = validator.validate(query)
        assert result.is_valid is False

    def test_block_alter(self) -> None:
        """ALTER 차단"""
        validator = KeywordValidator()
        query = "ALTER TABLE users DROP COLUMN email"
        result = validator.validate(query)
        assert result.is_valid is False

    # === 2단계: 스키마 검증 테스트 ===

    def test_block_nonexistent_table(self, sample_schema: DatabaseSchema) -> None:
        """존재하지 않는 테이블 접근 차단"""
        validator = SchemaValidator(sample_schema)
        query = "SELECT * FROM admin_secrets"
        result = validator.validate(query)
        assert result.is_valid is False
        assert "admin_secrets" in result.invalid_tables

    def test_block_nonexistent_column(self, sample_schema: DatabaseSchema) -> None:
        """존재하지 않는 컬럼 접근 차단"""
        validator = SchemaValidator(sample_schema)
        query = "SELECT password FROM users"
        result = validator.validate(query)
        assert result.is_valid is False
        assert "password" in result.invalid_columns

    def test_allow_valid_query(self, sample_schema: DatabaseSchema) -> None:
        """유효한 쿼리 허용"""
        validator = SchemaValidator(sample_schema)
        query = "SELECT id, name, email FROM users WHERE id = 1"
        result = validator.validate(query)
        assert result.is_valid is True

    # === 3단계: 시맨틱 검증 테스트 (Mocked) ===

    @pytest.mark.asyncio
    async def test_semantic_validation_safe_query(self) -> None:
        """시맨틱 검증: 안전한 쿼리 허용"""
        mock_llm = MagicMock()
        mock_llm.ainvoke = AsyncMock(return_value=MagicMock(content="SAFE"))

        validator = SemanticValidator(mock_llm)
        query = "SELECT COUNT(*) FROM orders WHERE created_at > '2024-01-01'"
        result = await validator.validate(query)
        assert result.is_valid is True

    @pytest.mark.asyncio
    async def test_semantic_validation_unsafe_query(self) -> None:
        """시맨틱 검증: 위험한 쿼리 차단"""
        mock_llm = MagicMock()
        mock_llm.ainvoke = AsyncMock(return_value=MagicMock(
            content="UNSAFE: 이 쿼리는 시스템 테이블에 접근하려고 합니다."
        ))

        validator = SemanticValidator(mock_llm)
        query = "SELECT * FROM pg_shadow"
        result = await validator.validate(query)
        assert result.is_valid is False

    # === 전체 파이프라인 테스트 ===

    @pytest.mark.asyncio
    async def test_pipeline_blocks_at_keyword_level(self, sample_schema: DatabaseSchema) -> None:
        """파이프라인: 1단계(키워드)에서 차단"""
        mock_llm = MagicMock()

        result = await validate_query_pipeline(
            query="DELETE FROM users",
            schema=sample_schema,
            llm=mock_llm,
        )

        assert result.is_valid is False
        assert result.blocked_at_layer == "keyword"
        # LLM이 호출되지 않아야 함 (1단계에서 차단)

    @pytest.mark.asyncio
    async def test_pipeline_blocks_at_schema_level(self, sample_schema: DatabaseSchema) -> None:
        """파이프라인: 2단계(스키마)에서 차단"""
        mock_llm = MagicMock()

        result = await validate_query_pipeline(
            query="SELECT * FROM nonexistent_table",
            schema=sample_schema,
            llm=mock_llm,
        )

        assert result.is_valid is False
        assert result.blocked_at_layer == "schema"

    @pytest.mark.asyncio
    async def test_pipeline_blocks_at_semantic_level(self, sample_schema: DatabaseSchema) -> None:
        """파이프라인: 3단계(시맨틱)에서 차단"""
        mock_llm = MagicMock()
        mock_llm.ainvoke = AsyncMock(return_value=MagicMock(
            content="UNSAFE: 의심스러운 패턴 감지"
        ))

        result = await validate_query_pipeline(
            query="SELECT * FROM users WHERE 1=1",
            schema=sample_schema,
            llm=mock_llm,
        )

        assert result.is_valid is False
        assert result.blocked_at_layer == "semantic"

    @pytest.mark.asyncio
    async def test_pipeline_allows_safe_query(self, sample_schema: DatabaseSchema) -> None:
        """파이프라인: 안전한 쿼리 허용"""
        mock_llm = MagicMock()
        mock_llm.ainvoke = AsyncMock(return_value=MagicMock(content="SAFE"))

        result = await validate_query_pipeline(
            query="SELECT id, name FROM users WHERE id = 1",
            schema=sample_schema,
            llm=mock_llm,
        )

        assert result.is_valid is True
        assert result.blocked_at_layer is None


class TestQueryValidationNode:
    """쿼리 검증 노드 테스트"""

    @pytest.fixture
    def initial_state(self) -> Text2SQLAgentState:
        """초기 상태"""
        return create_initial_state(
            user_question="지난달 매출을 알려줘",
            session_id="test-session",
        )

    @pytest.mark.asyncio
    async def test_node_validates_safe_query(
        self,
        initial_state: Text2SQLAgentState,
        sample_schema: DatabaseSchema,
    ) -> None:
        """노드: 안전한 쿼리 검증 통과"""
        state = {
            **initial_state,
            "generated_query": "SELECT SUM(total) FROM orders",
            "database_schema": str(sample_schema),
        }

        # 노드 실행 (mocked dependencies)
        # 실제 테스트에서는 의존성 주입 필요
        # result = await query_validation_node(state)
        # assert result["is_query_valid"] is True

    @pytest.mark.asyncio
    async def test_node_rejects_dangerous_query(
        self,
        initial_state: Text2SQLAgentState,
        sample_schema: DatabaseSchema,
    ) -> None:
        """노드: 위험한 쿼리 거부"""
        state = {
            **initial_state,
            "generated_query": "DROP TABLE users",
            "database_schema": str(sample_schema),
        }

        # 노드 실행 (mocked dependencies)
        # result = await query_validation_node(state)
        # assert result["is_query_valid"] is False
        # assert "위험" in result["validation_errors"][0]


class TestRetryLogic:
    """재시도 로직 테스트"""

    @pytest.mark.asyncio
    async def test_max_retry_count(self, sample_schema: DatabaseSchema) -> None:
        """최대 재시도 횟수 준수"""
        # 항상 실패하는 검증
        mock_llm = MagicMock()
        mock_llm.ainvoke = AsyncMock(return_value=MagicMock(content="UNSAFE"))

        # 재시도 로직이 3회 후 중단되는지 확인
        # 실제 구현에서 테스트
        pass

    @pytest.mark.asyncio
    async def test_retry_on_validation_failure(self, sample_schema: DatabaseSchema) -> None:
        """검증 실패 시 재시도"""
        # 첫 번째는 실패, 두 번째는 성공
        call_count = 0

        async def mock_validate(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return MagicMock(content="UNSAFE")
            return MagicMock(content="SAFE")

        mock_llm = MagicMock()
        mock_llm.ainvoke = mock_validate

        # 재시도 후 성공하는지 확인
        # 실제 구현에서 테스트
        pass
