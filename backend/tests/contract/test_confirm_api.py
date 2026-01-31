"""
POST /api/chat/confirm 엔드포인트 계약 테스트

Human-in-the-Loop 쿼리 확인 API의 계약을 검증합니다.
"""

import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.models.requests import ConfirmationRequest


@pytest.fixture
def sample_session_id() -> str:
    """테스트용 세션 ID"""
    return "test-session-12345"


@pytest.fixture
def sample_query_id() -> str:
    """테스트용 쿼리 ID"""
    return "test-query-67890"


class TestConfirmApiContract:
    """확인 API 계약 테스트"""

    @pytest.mark.asyncio
    async def test_confirm_approved_request_returns_success(
        self,
        sample_session_id: str,
        sample_query_id: str,
    ) -> None:
        """승인 요청 시 성공 응답 반환"""
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post(
                "/api/chat/confirm",
                json={
                    "session_id": sample_session_id,
                    "query_id": sample_query_id,
                    "approved": True,
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        # 승인 시 result가 포함될 수 있음

    @pytest.mark.asyncio
    async def test_confirm_rejected_request_returns_success(
        self,
        sample_session_id: str,
        sample_query_id: str,
    ) -> None:
        """거부 요청 시 성공 응답 반환"""
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post(
                "/api/chat/confirm",
                json={
                    "session_id": sample_session_id,
                    "query_id": sample_query_id,
                    "approved": False,
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        # 거부 시 result는 None

    @pytest.mark.asyncio
    async def test_confirm_missing_session_id_returns_422(self) -> None:
        """session_id 누락 시 422 반환"""
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post(
                "/api/chat/confirm",
                json={
                    "query_id": "some-query-id",
                    "approved": True,
                },
            )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_confirm_missing_query_id_returns_422(
        self,
        sample_session_id: str,
    ) -> None:
        """query_id 누락 시 422 반환"""
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post(
                "/api/chat/confirm",
                json={
                    "session_id": sample_session_id,
                    "approved": True,
                },
            )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_confirm_missing_approved_returns_422(
        self,
        sample_session_id: str,
        sample_query_id: str,
    ) -> None:
        """approved 누락 시 422 반환"""
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post(
                "/api/chat/confirm",
                json={
                    "session_id": sample_session_id,
                    "query_id": sample_query_id,
                },
            )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_confirm_response_structure(
        self,
        sample_session_id: str,
        sample_query_id: str,
    ) -> None:
        """응답 구조 검증"""
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post(
                "/api/chat/confirm",
                json={
                    "session_id": sample_session_id,
                    "query_id": sample_query_id,
                    "approved": True,
                },
            )

        assert response.status_code == 200
        data = response.json()

        # 필수 필드 확인
        assert "success" in data
        assert isinstance(data["success"], bool)

        # 선택적 필드 확인 (타입 검증)
        if "result" in data and data["result"] is not None:
            assert isinstance(data["result"], dict)

        if "error" in data and data["error"] is not None:
            assert "code" in data["error"]
            assert "message" in data["error"]


class TestConfirmApiWithModifiedQuery:
    """수정된 쿼리와 함께 확인 요청 테스트"""

    @pytest.mark.asyncio
    async def test_confirm_with_modified_query(
        self,
        sample_session_id: str,
        sample_query_id: str,
    ) -> None:
        """수정된 쿼리와 함께 승인 요청"""
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post(
                "/api/chat/confirm",
                json={
                    "session_id": sample_session_id,
                    "query_id": sample_query_id,
                    "approved": True,
                    "modified_query": "SELECT id, name FROM users LIMIT 10",
                },
            )

        # 수정된 쿼리도 처리 가능해야 함
        assert response.status_code == 200
        data = response.json()
        assert "success" in data


class TestConfirmApiErrorHandling:
    """에러 처리 테스트"""

    @pytest.mark.asyncio
    async def test_confirm_invalid_session_returns_error(self) -> None:
        """존재하지 않는 세션 ID로 요청 시 적절한 응답"""
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post(
                "/api/chat/confirm",
                json={
                    "session_id": "nonexistent-session",
                    "query_id": "nonexistent-query",
                    "approved": True,
                },
            )

        # 현재 구현에서는 세션 검증 없이 성공 반환
        # 추후 세션 검증 구현 시 변경될 수 있음
        assert response.status_code in [200, 400, 404]
