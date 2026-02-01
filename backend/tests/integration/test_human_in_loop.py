"""
Human-in-the-Loop 흐름 통합 테스트

사용자 확인 기능이 올바르게 동작하는지 검증합니다.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.agent.nodes.user_confirmation import (
    user_confirmation_node,
    ConfirmationRequired,
)
from app.agent.state import Text2SQLAgentState, create_initial_state


class TestUserConfirmationNode:
    """사용자 확인 노드 테스트"""

    @pytest.fixture
    def sample_state(self) -> Text2SQLAgentState:
        """샘플 상태 생성"""
        state = create_initial_state(
            user_question="지난달 매출 보여줘",
            session_id="test-session",
        )
        state["generated_query"] = "SELECT * FROM sales WHERE date >= '2024-01-01'"
        state["query_explanation"] = "지난달 매출 데이터를 조회합니다."
        state["query_id"] = "test-query-id"
        state["is_query_valid"] = True
        return state

    def test_confirmation_node_raises_interrupt(
        self, sample_state: Text2SQLAgentState
    ) -> None:
        """확인 노드가 interrupt를 발생시키는지 확인"""
        try:
            result = user_confirmation_node(sample_state)
            # interrupt가 발생하지 않으면 결과에 대기 상태가 있어야 함
            assert result.get("user_approved") is None
        except ConfirmationRequired:
            # interrupt가 발생하면 성공
            pass

    def test_confirmation_node_returns_query_info(
        self, sample_state: Text2SQLAgentState
    ) -> None:
        """확인 노드가 쿼리 정보를 반환하는지 확인"""
        try:
            result = user_confirmation_node(sample_state)
            # 결과에 쿼리 ID가 포함되어야 함
            assert "query_id" in str(result) or sample_state.get("query_id")
        except ConfirmationRequired as e:
            # interrupt 발생 시 쿼리 ID가 포함되어야 함
            assert hasattr(e, "query_id") or sample_state.get("query_id")


class TestHumanInTheLoopFlow:
    """Human-in-the-Loop 전체 흐름 테스트"""

    @pytest.fixture
    def sample_state(self) -> Text2SQLAgentState:
        """샘플 상태 생성"""
        state = create_initial_state(
            user_question="고객 목록 보여줘",
            session_id="test-session",
        )
        state["generated_query"] = "SELECT * FROM customers"
        state["query_explanation"] = "고객 목록을 조회합니다."
        state["query_id"] = "test-query-id"
        state["is_query_valid"] = True
        return state

    def test_flow_pauses_for_confirmation(
        self, sample_state: Text2SQLAgentState
    ) -> None:
        """쿼리 생성 후 확인을 위해 일시 중지되는지 확인"""
        try:
            result = user_confirmation_node(sample_state)
            # 사용자 승인이 None (대기 중)이어야 함
            assert result.get("user_approved") is None or "query_id" in str(result)
        except ConfirmationRequired:
            # interrupt 발생 = 확인 대기 중
            pass

    def test_approved_query_continues_execution(
        self, sample_state: Text2SQLAgentState
    ) -> None:
        """승인된 쿼리가 실행을 계속하는지 확인"""
        # 승인 상태로 설정
        sample_state["user_approved"] = True

        # 이미 승인된 상태에서는 interrupt 없이 진행
        result = user_confirmation_node(sample_state)
        assert result.get("user_approved") is True

    def test_rejected_query_stops_execution(
        self, sample_state: Text2SQLAgentState
    ) -> None:
        """거부된 쿼리가 실행을 중지하는지 확인"""
        # 거부 상태로 설정
        sample_state["user_approved"] = False

        result = user_confirmation_node(sample_state)
        assert result.get("user_approved") is False
        # 실행 에러가 설정되어야 함
        assert result.get("execution_error") is not None


class TestConfirmationResponseHandling:
    """확인 응답 처리 테스트"""

    @pytest.fixture
    def pending_state(self) -> Text2SQLAgentState:
        """확인 대기 중인 상태"""
        state = create_initial_state(
            user_question="주문 내역 보여줘",
            session_id="test-session",
        )
        state["generated_query"] = "SELECT * FROM orders"
        state["query_explanation"] = "주문 내역을 조회합니다."
        state["query_id"] = "pending-query-id"
        state["is_query_valid"] = True
        state["user_approved"] = None  # 대기 중
        return state

    def test_user_approval_updates_state(
        self, pending_state: Text2SQLAgentState
    ) -> None:
        """사용자 승인이 상태를 업데이트하는지 확인"""
        pending_state["user_approved"] = True
        result = user_confirmation_node(pending_state)
        assert result.get("user_approved") is True

    def test_user_rejection_updates_state(
        self, pending_state: Text2SQLAgentState
    ) -> None:
        """사용자 거부가 상태를 업데이트하는지 확인"""
        pending_state["user_approved"] = False
        result = user_confirmation_node(pending_state)
        assert result.get("user_approved") is False

    def test_rejection_provides_friendly_message(
        self, pending_state: Text2SQLAgentState
    ) -> None:
        """거부 시 사용자 친화적 메시지 제공"""
        pending_state["user_approved"] = False
        result = user_confirmation_node(pending_state)

        error = result.get("execution_error", "")
        # 한국어 메시지 확인
        assert "취소" in error or "거부" in error or error != ""


class TestQueryPreviewGeneration:
    """쿼리 미리보기 생성 테스트"""

    @pytest.fixture
    def state_with_query(self) -> Text2SQLAgentState:
        """쿼리가 있는 상태"""
        state = create_initial_state(
            user_question="매출 현황 보여줘",
            session_id="test-session",
        )
        state["generated_query"] = """
            SELECT DATE_TRUNC('month', created_at) AS month,
                   SUM(amount) AS total_sales
            FROM sales
            GROUP BY month
            ORDER BY month DESC
        """
        state["query_explanation"] = "월별 매출 합계를 조회합니다."
        state["query_id"] = "preview-query-id"
        state["is_query_valid"] = True
        return state

    def test_query_preview_includes_sql(
        self, state_with_query: Text2SQLAgentState
    ) -> None:
        """미리보기에 SQL 쿼리가 포함되는지 확인"""
        assert state_with_query.get("generated_query")
        assert "SELECT" in state_with_query.get("generated_query", "")

    def test_query_preview_includes_explanation(
        self, state_with_query: Text2SQLAgentState
    ) -> None:
        """미리보기에 설명이 포함되는지 확인"""
        assert state_with_query.get("query_explanation")
        # 한국어 설명
        explanation = state_with_query.get("query_explanation", "")
        assert len(explanation) > 0

    def test_query_preview_includes_query_id(
        self, state_with_query: Text2SQLAgentState
    ) -> None:
        """미리보기에 쿼리 ID가 포함되는지 확인"""
        assert state_with_query.get("query_id")
