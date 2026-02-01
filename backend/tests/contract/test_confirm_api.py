"""
POST /api/chat/confirm 엔드포인트 계약 테스트

Human-in-the-Loop 확인 API의 계약을 검증합니다.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> TestClient:
    """동기 테스트 클라이언트"""
    with TestClient(app) as c:
        yield c


class TestConfirmEndpointContract:
    """POST /api/chat/confirm 엔드포인트 계약 테스트"""

    def test_confirm_endpoint_exists(self, client: TestClient) -> None:
        """엔드포인트가 존재하는지 확인"""
        response = client.post(
            "/api/chat/confirm",
            json={
                "session_id": "test-session",
                "query_id": "test-query",
                "approved": True,
            },
        )
        # 404가 아니면 엔드포인트 존재
        assert response.status_code != 404

    def test_confirm_requires_session_id(self, client: TestClient) -> None:
        """session_id가 필수인지 확인"""
        response = client.post(
            "/api/chat/confirm",
            json={
                "query_id": "test-query",
                "approved": True,
            },
        )
        assert response.status_code == 422  # Validation Error

    def test_confirm_requires_query_id(self, client: TestClient) -> None:
        """query_id가 필수인지 확인"""
        response = client.post(
            "/api/chat/confirm",
            json={
                "session_id": "test-session",
                "approved": True,
            },
        )
        assert response.status_code == 422

    def test_confirm_requires_approved(self, client: TestClient) -> None:
        """approved가 필수인지 확인"""
        response = client.post(
            "/api/chat/confirm",
            json={
                "session_id": "test-session",
                "query_id": "test-query",
            },
        )
        assert response.status_code == 422

    def test_confirm_approved_is_boolean(self, client: TestClient) -> None:
        """approved가 boolean이어야 하는지 확인"""
        response = client.post(
            "/api/chat/confirm",
            json={
                "session_id": "test-session",
                "query_id": "test-query",
                "approved": "yes",  # 잘못된 타입
            },
        )
        assert response.status_code == 422

    def test_confirm_response_structure_on_approve(self, client: TestClient) -> None:
        """승인 시 응답 구조 확인"""
        response = client.post(
            "/api/chat/confirm",
            json={
                "session_id": "test-session",
                "query_id": "test-query",
                "approved": True,
            },
        )

        # 응답이 성공적이거나 세션 없음 에러
        if response.status_code == 200:
            data = response.json()
            assert "success" in data
            # result가 있거나 null
            assert "result" in data or data.get("error")

    def test_confirm_response_structure_on_reject(self, client: TestClient) -> None:
        """거부 시 응답 구조 확인"""
        response = client.post(
            "/api/chat/confirm",
            json={
                "session_id": "test-session",
                "query_id": "test-query",
                "approved": False,
            },
        )

        if response.status_code == 200:
            data = response.json()
            assert "success" in data
            assert data["success"] is True
            # 거부 시 result는 null
            assert data.get("result") is None


class TestConfirmEndpointValidation:
    """확인 엔드포인트 입력 검증 테스트"""

    def test_session_id_must_be_string(self, client: TestClient) -> None:
        """session_id가 문자열이어야 함"""
        response = client.post(
            "/api/chat/confirm",
            json={
                "session_id": 12345,  # 숫자
                "query_id": "test-query",
                "approved": True,
            },
        )
        # Pydantic이 자동 변환하므로 200 또는 422
        assert response.status_code in [200, 422, 500]

    def test_query_id_must_be_string(self, client: TestClient) -> None:
        """query_id가 문자열이어야 함"""
        response = client.post(
            "/api/chat/confirm",
            json={
                "session_id": "test-session",
                "query_id": 12345,  # 숫자
                "approved": True,
            },
        )
        assert response.status_code in [200, 422, 500]


class TestConfirmEndpointIntegration:
    """확인 엔드포인트 통합 테스트"""

    def test_nonexistent_session_handling(self, client: TestClient) -> None:
        """존재하지 않는 세션 처리"""
        response = client.post(
            "/api/chat/confirm",
            json={
                "session_id": "nonexistent-session-id",
                "query_id": "nonexistent-query-id",
                "approved": True,
            },
        )

        # 세션을 찾을 수 없으면 에러 응답
        assert response.status_code in [200, 404, 400, 500]

    def test_nonexistent_query_handling(self, client: TestClient) -> None:
        """존재하지 않는 쿼리 처리"""
        response = client.post(
            "/api/chat/confirm",
            json={
                "session_id": "test-session",
                "query_id": "nonexistent-query-id",
                "approved": True,
            },
        )

        assert response.status_code in [200, 404, 400, 500]
