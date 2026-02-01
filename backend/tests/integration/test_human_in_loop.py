"""
Human-in-the-Loop 흐름 통합 테스트

사용자 확인 단계가 포함된 전체 워크플로우를 테스트합니다.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

from app.agent.graph import build_graph, compile_graph
from app.agent.state import Text2SQLAgentState, create_initial_state
from app.models.entities import DatabaseSchema, TableInfo, SchemaColumnInfo


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
                ],
                estimated_row_count=100,
            ),
        ],
    )


@pytest.fixture
def initial_state() -> Text2SQLAgentState:
    """초기 에이전트 상태"""
    return create_initial_state(
        user_question="사용자 목록을 보여줘",
        session_id="test-session",
    )


class TestHumanInLoopWorkflow:
    """Human-in-the-Loop 워크플로우 테스트"""

    @pytest.mark.asyncio
    async def test_workflow_pauses_for_user_confirmation(
        self,
        initial_state: Text2SQLAgentState,
    ) -> None:
        """워크플로우가 사용자 확인을 위해 일시 중지되는지 확인"""
        # 이 테스트는 interrupt 구현 후 활성화
        # 현재는 자동 실행 모드
        pass

    @pytest.mark.asyncio
    async def test_workflow_continues_after_approval(
        self,
        initial_state: Text2SQLAgentState,
    ) -> None:
        """사용자 승인 후 워크플로우가 계속되는지 확인"""
        # Command(resume)로 재개되는지 확인
        pass

    @pytest.mark.asyncio
    async def test_workflow_stops_after_rejection(
        self,
        initial_state: Text2SQLAgentState,
    ) -> None:
        """사용자 거부 후 워크플로우가 중지되는지 확인"""
        # 거부 시 적절한 응답과 함께 종료
        pass


class TestUserConfirmationNode:
    """사용자 확인 노드 테스트"""

    @pytest.mark.asyncio
    async def test_node_generates_confirmation_request(self) -> None:
        """노드가 확인 요청을 생성하는지 확인"""
        from app.agent.nodes.user_confirmation import user_confirmation_node

        state: Text2SQLAgentState = {
            "user_question": "사용자 목록을 보여줘",
            "session_id": "test-session",
            "messages": [],
            "database_schema": "",
            "relevant_tables": ["users"],
            "generated_query": "SELECT * FROM users",
            "query_explanation": "모든 사용자를 조회합니다.",
            "generation_attempt": 1,
            "validation_errors": [],
            "is_query_valid": True,
            "user_approved": None,
            "query_id": "test-query-id",
            "query_result": [],
            "result_columns": [],
            "total_row_count": 0,
            "execution_time_ms": 0,
            "execution_error": None,
            "final_response": "",
            "response_format": "table",
        }

        # 노드 실행
        # Human-in-the-Loop 구현에서는 interrupt가 발생
        # result = await user_confirmation_node(state)
        # assert result.get("user_approved") is None  # 대기 상태

    @pytest.mark.asyncio
    async def test_node_handles_approval(self) -> None:
        """승인 처리 확인"""
        from app.agent.nodes.user_confirmation import handle_user_response

        state: Text2SQLAgentState = {
            "user_question": "사용자 목록을 보여줘",
            "session_id": "test-session",
            "messages": [],
            "database_schema": "",
            "relevant_tables": ["users"],
            "generated_query": "SELECT * FROM users",
            "query_explanation": "모든 사용자를 조회합니다.",
            "generation_attempt": 1,
            "validation_errors": [],
            "is_query_valid": True,
            "user_approved": None,
            "query_id": "test-query-id",
            "query_result": [],
            "result_columns": [],
            "total_row_count": 0,
            "execution_time_ms": 0,
            "execution_error": None,
            "final_response": "",
            "response_format": "table",
        }

        result = handle_user_response(state, approved=True)
        assert result["user_approved"] is True

    @pytest.mark.asyncio
    async def test_node_handles_rejection(self) -> None:
        """거부 처리 확인"""
        from app.agent.nodes.user_confirmation import handle_user_response

        state: Text2SQLAgentState = {
            "user_question": "사용자 목록을 보여줘",
            "session_id": "test-session",
            "messages": [],
            "database_schema": "",
            "relevant_tables": ["users"],
            "generated_query": "SELECT * FROM users",
            "query_explanation": "모든 사용자를 조회합니다.",
            "generation_attempt": 1,
            "validation_errors": [],
            "is_query_valid": True,
            "user_approved": None,
            "query_id": "test-query-id",
            "query_result": [],
            "result_columns": [],
            "total_row_count": 0,
            "execution_time_ms": 0,
            "execution_error": None,
            "final_response": "",
            "response_format": "table",
        }

        result = handle_user_response(state, approved=False)
        assert result["user_approved"] is False


class TestQueryPreviewGeneration:
    """쿼리 미리보기 생성 테스트"""

    @pytest.mark.asyncio
    async def test_query_explanation_generated(self) -> None:
        """쿼리 설명이 생성되는지 확인"""
        # query_generation_node에서 설명이 함께 생성되는지 확인
        pass

    @pytest.mark.asyncio
    async def test_query_explanation_in_korean(self) -> None:
        """쿼리 설명이 한국어인지 확인"""
        # 설명이 한국어로 생성되는지 확인
        pass


class TestModifiedQueryExecution:
    """수정된 쿼리 실행 테스트"""

    @pytest.mark.asyncio
    async def test_execute_modified_query(self) -> None:
        """사용자가 수정한 쿼리 실행"""
        # modified_query가 있을 때 해당 쿼리로 실행되는지 확인
        pass

    @pytest.mark.asyncio
    async def test_modified_query_validation(self) -> None:
        """수정된 쿼리도 검증되는지 확인"""
        # 수정된 쿼리도 3단계 검증을 거치는지 확인
        pass


class TestAutoConfirmMode:
    """자동 확인 모드 테스트"""

    @pytest.mark.asyncio
    async def test_auto_confirm_enabled(self) -> None:
        """자동 확인 모드가 활성화된 경우 바로 실행"""
        # auto_confirm=True일 때 확인 단계 건너뜀
        pass

    @pytest.mark.asyncio
    async def test_auto_confirm_disabled_pauses(self) -> None:
        """자동 확인 모드가 비활성화된 경우 일시 중지"""
        # auto_confirm=False일 때 확인 대기
        pass
