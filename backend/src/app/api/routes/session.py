"""
세션 관리 API 엔드포인트

세션 생성, 조회, 종료를 위한 REST API입니다.
"""

import logging

from fastapi import APIRouter, HTTPException, status

from app.errors.exceptions import SessionExpiredError, SessionNotFoundError
from app.models.requests import CreateSessionRequest
from app.models.responses import SessionResponse
from app.session import manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sessions")


@router.post(
    "",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="새 세션 생성",
    description="새로운 대화 세션을 생성합니다.",
)
async def create_session(
    request: CreateSessionRequest = CreateSessionRequest(),
) -> SessionResponse:
    """
    새 세션 생성

    Args:
        request: 세션 생성 요청 (LLM 제공자 선택)

    Returns:
        SessionResponse: 생성된 세션 정보
    """
    session = manager.create_session(
        llm_provider=request.llm_provider,
    )

    logger.info(f"세션 생성 완료: {session.session_id}")

    return SessionResponse(
        session_id=session.session_id,
        status=session.status,
        llm_provider=session.llm_provider.value,  # type: ignore[arg-type]
        created_at=session.created_at,
        last_activity_at=session.last_activity_at,
        message_history=session.message_history[-10:],  # 최근 10개만
    )


@router.get(
    "/{session_id}",
    response_model=SessionResponse,
    summary="세션 조회",
    description="세션 ID로 세션 정보를 조회합니다.",
)
async def get_session(session_id: str) -> SessionResponse:
    """
    세션 조회

    Args:
        session_id: 세션 ID

    Returns:
        SessionResponse: 세션 정보

    Raises:
        HTTPException: 세션을 찾을 수 없거나 만료된 경우
    """
    try:
        session = manager.get_session(session_id)
    except SessionNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "SESSION_NOT_FOUND", "message": "세션을 찾을 수 없습니다."},
        )
    except SessionExpiredError:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail={"code": "SESSION_EXPIRED", "message": "세션이 만료되었습니다."},
        )

    return SessionResponse(
        session_id=session.session_id,
        status=session.status,
        llm_provider=session.llm_provider.value,  # type: ignore[arg-type]
        created_at=session.created_at,
        last_activity_at=session.last_activity_at,
        message_history=session.message_history[-10:],
    )


@router.delete(
    "/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="세션 종료",
    description="세션을 종료합니다.",
)
async def terminate_session(session_id: str) -> None:
    """
    세션 종료

    Args:
        session_id: 종료할 세션 ID
    """
    manager.terminate_session(session_id)
    logger.info(f"세션 종료 완료: {session_id}")
