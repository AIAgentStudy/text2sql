"""
대화 맥락 유지 통합 테스트

연속 질문에서 이전 대화 맥락이 유지되는지 테스트합니다.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from langchain_core.messages import HumanMessage, AIMessage

from app.agent.state import Text2SQLAgentState, create_initial_state
from app.agent.nodes.query_generation import (
    query_generation_node,
    detect_context_reference,
    build_context_aware_prompt,
    CONTEXT_REFERENCE_PATTERNS,
)
from app.session.manager import (
    create_session,
    add_message_to_session,
    get_session,
    reset_session,
    get_or_create_session,
)


class TestContextReferenceDetection:
    """맥락 참조 감지 테스트"""

    def test_detect_context_reference_korean(self) -> None:
        """한국어 맥락 참조 감지"""
        # 맥락 참조가 있는 질문들
        context_queries = [
            "그중에 서울 지역만 보여줘",
            "거기서 상위 10개만",
            "위에서 말한 것 중에 2024년만",
            "이전 결과에서 금액이 100만원 이상인 것",
            "방금 그거 다시 보여줘",
            "아까 그 데이터 중에서",
        ]

        for query in context_queries:
            result = detect_context_reference(query)
            assert result is True, f"'{query}'에서 맥락 참조를 감지하지 못함"

    def test_no_context_reference(self) -> None:
        """맥락 참조가 없는 질문"""
        standalone_queries = [
            "지난달 매출을 보여줘",
            "고객 목록을 조회해줘",
            "2024년 1월 주문 건수는?",
            "상품 카테고리별 판매량",
        ]

        for query in standalone_queries:
            result = detect_context_reference(query)
            assert result is False, f"'{query}'에서 잘못된 맥락 참조 감지"


class TestConversationHistoryManagement:
    """대화 히스토리 관리 테스트"""

    def test_session_message_history(self) -> None:
        """세션에 메시지 히스토리 저장"""
        session = create_session()
        session_id = session.session_id

        # 메시지 추가
        add_message_to_session(session_id, "user", "지난달 매출 보여줘")
        add_message_to_session(session_id, "assistant", "지난달 매출은 1억원입니다.")
        add_message_to_session(session_id, "user", "그중에 서울 지역만")

        # 히스토리 확인
        session = get_session(session_id)
        assert len(session.message_history) == 3
        assert session.message_history[0].role == "user"
        assert session.message_history[0].content == "지난달 매출 보여줘"
        assert session.message_history[2].content == "그중에 서울 지역만"

    def test_session_reset_clears_history(self) -> None:
        """세션 초기화 시 히스토리 삭제"""
        session = create_session()
        session_id = session.session_id

        # 메시지 추가
        add_message_to_session(session_id, "user", "테스트 메시지")

        # 세션 초기화
        reset_session(session_id)

        # 히스토리 확인
        session = get_session(session_id)
        assert len(session.message_history) == 0

    def test_message_history_limit(self) -> None:
        """메시지 히스토리 최대 개수 제한"""
        session = create_session()
        session_id = session.session_id

        # 많은 메시지 추가
        for i in range(20):
            add_message_to_session(session_id, "user", f"메시지 {i}")

        # 히스토리 확인 (설정의 max_message_history에 맞게 제한됨)
        session = get_session(session_id)
        assert len(session.message_history) <= 10  # 기본값


class TestContextAwareQueryGeneration:
    """맥락 인식 쿼리 생성 테스트"""

    @pytest.mark.asyncio
    async def test_context_aware_prompt_includes_history(self) -> None:
        """맥락 인식 프롬프트에 히스토리 포함"""
        messages = [
            HumanMessage(content="지난달 매출 보여줘"),
            AIMessage(content="SELECT SUM(amount) FROM sales WHERE date >= '2024-01-01'"),
        ]

        current_question = "그중에 서울 지역만"

        prompt = build_context_aware_prompt(
            current_question=current_question,
            message_history=messages,
            schema="테이블: sales (id, amount, date, region)",
        )

        # 프롬프트에 이전 대화가 포함되어야 함
        assert "지난달 매출" in prompt or "이전 질문" in prompt

    @pytest.mark.asyncio
    async def test_query_generation_uses_context(self) -> None:
        """쿼리 생성 시 맥락 활용"""
        # Mocked LLM
        mock_llm = MagicMock()
        mock_llm.ainvoke = AsyncMock(return_value=MagicMock(
            content="""SQL:
```sql
SELECT SUM(amount) FROM sales WHERE date >= '2024-01-01' AND region = '서울'
```

설명:
지난달 매출 중 서울 지역만 필터링하여 조회합니다."""
        ))

        state: Text2SQLAgentState = {
            "user_question": "그중에 서울 지역만",
            "session_id": "test-session",
            "messages": [
                HumanMessage(content="지난달 매출 보여줘"),
                AIMessage(content="지난달 매출은 1억원입니다."),
            ],
            "database_schema": "테이블: sales",
            "relevant_tables": [],
            "generated_query": "",
            "query_explanation": "",
            "generation_attempt": 0,
            "validation_errors": [],
            "is_query_valid": False,
            "user_approved": None,
            "query_id": "",
            "query_result": [],
            "result_columns": [],
            "total_row_count": 0,
            "execution_time_ms": 0,
            "execution_error": None,
            "final_response": "",
            "response_format": "table",
        }

        with patch("app.agent.nodes.query_generation.get_chat_model", return_value=mock_llm):
            result = await query_generation_node(state)

        # 쿼리가 생성되어야 함
        assert result.get("generated_query")
        # 서울 지역 필터가 포함되어야 함
        assert "서울" in result.get("generated_query", "")


class TestResetCommand:
    """처음부터 다시 명령어 테스트"""

    def test_reset_command_detection(self) -> None:
        """리셋 명령어 감지"""
        from app.agent.nodes.query_generation import is_reset_command

        reset_commands = [
            "처음부터 다시",
            "다시 시작",
            "새로운 대화",
            "리셋",
            "초기화",
            "대화 초기화",
        ]

        for cmd in reset_commands:
            assert is_reset_command(cmd) is True, f"'{cmd}'를 리셋 명령어로 인식하지 못함"

    def test_normal_query_not_reset(self) -> None:
        """일반 질문은 리셋 명령이 아님"""
        from app.agent.nodes.query_generation import is_reset_command

        normal_queries = [
            "매출 보여줘",
            "처음 가입한 고객은?",
            "다시 조회해줘",  # 맥락 있는 재조회
        ]

        for query in normal_queries:
            assert is_reset_command(query) is False, f"'{query}'를 리셋 명령어로 잘못 인식"


class TestSequentialQueries:
    """연속 질문 시나리오 테스트"""

    @pytest.mark.asyncio
    async def test_followup_query_uses_previous_result(self) -> None:
        """후속 질문에서 이전 결과 활용"""
        # 시나리오: "지난달 매출 보여줘" → "그중에 서울 지역만"
        # 두 번째 질문은 첫 번째 결과를 참조해야 함
        pass

    @pytest.mark.asyncio
    async def test_multiple_followup_queries(self) -> None:
        """다단계 후속 질문"""
        # 시나리오:
        # 1. "지난달 매출 보여줘"
        # 2. "그중에 서울 지역만"
        # 3. "거기서 상위 10개만"
        pass

    @pytest.mark.asyncio
    async def test_context_lost_after_reset(self) -> None:
        """리셋 후 맥락 초기화 확인"""
        # 시나리오:
        # 1. "지난달 매출 보여줘"
        # 2. "처음부터 다시"
        # 3. "그중에 서울만" → 맥락 없어서 오류 또는 새 질문으로 처리
        pass


class TestSessionTimeout:
    """세션 타임아웃 테스트"""

    def test_session_expiry_check(self) -> None:
        """세션 만료 확인"""
        from datetime import datetime, timedelta

        session = create_session()
        session_id = session.session_id

        # 세션이 활성 상태인지 확인
        session = get_session(session_id)
        assert session is not None

    def test_expired_session_creates_new(self) -> None:
        """만료된 세션 접근 시 새 세션 생성"""
        # get_or_create_session은 만료된 세션에 대해 새 세션 생성
        session = get_or_create_session("nonexistent-session-id")
        assert session is not None
        assert session.session_id != "nonexistent-session-id"
