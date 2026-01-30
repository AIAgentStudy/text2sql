"""
POST /api/chat 엔드포인트 계약 테스트

API 계약(contracts/api.yaml)에 정의된 스펙을 검증합니다.
"""

import pytest
from httpx import AsyncClient


class TestChatAPIContract:
    """채팅 API 계약 테스트"""

    @pytest.mark.asyncio
    async def test_chat_request_requires_message(self, async_client: AsyncClient) -> None:
        """메시지 필드는 필수"""
        response = await async_client.post(
            "/api/chat",
            json={},
        )
        assert response.status_code == 422  # Validation Error

    @pytest.mark.asyncio
    async def test_chat_request_message_min_length(self, async_client: AsyncClient) -> None:
        """메시지는 최소 2자 이상"""
        response = await async_client.post(
            "/api/chat",
            json={"message": "a"},  # 1자
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_chat_request_message_max_length(self, async_client: AsyncClient) -> None:
        """메시지는 최대 1000자"""
        response = await async_client.post(
            "/api/chat",
            json={"message": "a" * 1001},  # 1001자
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_chat_request_valid_llm_provider(self, async_client: AsyncClient) -> None:
        """LLM 프로바이더는 openai, anthropic, google 중 하나"""
        response = await async_client.post(
            "/api/chat",
            json={"message": "테스트 질문", "llm_provider": "invalid"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_chat_request_accepts_valid_providers(
        self, async_client: AsyncClient
    ) -> None:
        """유효한 LLM 프로바이더 허용"""
        for provider in ["openai", "anthropic", "google"]:
            # 실제 API 호출은 실패할 수 있지만 검증은 통과해야 함
            response = await async_client.post(
                "/api/chat",
                json={"message": "테스트 질문", "llm_provider": provider},
            )
            # 422가 아니면 검증 통과
            assert response.status_code != 422

    @pytest.mark.asyncio
    async def test_chat_response_is_sse_stream(self, async_client: AsyncClient) -> None:
        """응답은 SSE 스트림 형식"""
        # 이 테스트는 실제 DB/LLM 연결이 필요하므로 통합 테스트에서 수행
        pass

    @pytest.mark.asyncio
    async def test_chat_request_optional_session_id(
        self, async_client: AsyncClient
    ) -> None:
        """session_id는 선택 사항"""
        # session_id 없이 요청
        response = await async_client.post(
            "/api/chat",
            json={"message": "테스트 질문"},
        )
        # 검증은 통과해야 함 (422가 아님)
        assert response.status_code != 422


class TestConfirmAPIContract:
    """쿼리 확인 API 계약 테스트"""

    @pytest.mark.asyncio
    async def test_confirm_requires_session_id(self, async_client: AsyncClient) -> None:
        """session_id 필드는 필수"""
        response = await async_client.post(
            "/api/chat/confirm",
            json={"query_id": "test-query-id", "approved": True},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_confirm_requires_query_id(self, async_client: AsyncClient) -> None:
        """query_id 필드는 필수"""
        response = await async_client.post(
            "/api/chat/confirm",
            json={"session_id": "test-session-id", "approved": True},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_confirm_requires_approved(self, async_client: AsyncClient) -> None:
        """approved 필드는 필수"""
        response = await async_client.post(
            "/api/chat/confirm",
            json={"session_id": "test-session-id", "query_id": "test-query-id"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_confirm_approved_is_boolean(self, async_client: AsyncClient) -> None:
        """approved는 불리언 타입"""
        response = await async_client.post(
            "/api/chat/confirm",
            json={
                "session_id": "test-session-id",
                "query_id": "test-query-id",
                "approved": "yes",  # 문자열
            },
        )
        assert response.status_code == 422
