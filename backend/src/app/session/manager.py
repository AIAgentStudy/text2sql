"""
세션 관리자

대화 세션의 생성, 조회, 만료를 관리합니다.
"""

import logging
import uuid
from datetime import datetime, timedelta

from langgraph.checkpoint.memory import InMemorySaver

from app.config import get_settings
from app.errors.exceptions import SessionExpiredError, SessionNotFoundError
from app.models.entities import ConversationSession, LLMProvider, Message, SessionStatus

logger = logging.getLogger(__name__)

# 인메모리 세션 저장소
_sessions: dict[str, ConversationSession] = {}

# LangGraph 체크포인터
_checkpointer = InMemorySaver()


def get_checkpointer() -> InMemorySaver:
    """LangGraph 체크포인터 반환"""
    return _checkpointer


def create_session(
    llm_provider: str = "openai",
    user_id: str | None = None,
) -> ConversationSession:
    """
    새 세션 생성

    Args:
        llm_provider: 사용할 LLM 프로바이더
        user_id: 사용자 ID (선택)

    Returns:
        생성된 세션
    """
    session_id = str(uuid.uuid4())
    now = datetime.utcnow()

    # LLM 프로바이더 검증
    try:
        provider = LLMProvider(llm_provider)
    except ValueError:
        provider = LLMProvider.OPENAI

    session = ConversationSession(
        session_id=session_id,
        user_id=user_id,
        created_at=now,
        last_activity_at=now,
        status=SessionStatus.ACTIVE,
        llm_provider=provider,
        message_history=[],
    )

    _sessions[session_id] = session
    logger.info(f"새 세션 생성: {session_id}")

    return session


def get_session(session_id: str) -> ConversationSession:
    """
    세션 조회

    Args:
        session_id: 세션 ID

    Returns:
        세션 정보

    Raises:
        SessionNotFoundError: 세션을 찾을 수 없을 때
        SessionExpiredError: 세션이 만료되었을 때
    """
    if session_id not in _sessions:
        raise SessionNotFoundError(session_id)

    session = _sessions[session_id]

    # 만료 확인
    if _is_session_expired(session):
        session.status = SessionStatus.EXPIRED
        raise SessionExpiredError(session_id)

    if session.status == SessionStatus.TERMINATED:
        raise SessionNotFoundError(session_id)

    return session


def update_session_activity(session_id: str) -> ConversationSession:
    """
    세션 활동 시간 업데이트

    Args:
        session_id: 세션 ID

    Returns:
        업데이트된 세션
    """
    session = get_session(session_id)
    session.last_activity_at = datetime.utcnow()
    return session


def add_message_to_session(
    session_id: str,
    role: str,
    content: str,
) -> ConversationSession:
    """
    세션에 메시지 추가

    Args:
        session_id: 세션 ID
        role: 메시지 역할 (user, assistant, system)
        content: 메시지 내용

    Returns:
        업데이트된 세션
    """
    session = get_session(session_id)
    settings = get_settings()

    # 메시지 추가
    message = Message(
        role=role,  # type: ignore[arg-type]
        content=content,
        timestamp=datetime.utcnow(),
    )
    session.message_history.append(message)

    # 최대 메시지 수 제한
    if len(session.message_history) > settings.max_message_history:
        session.message_history = session.message_history[-settings.max_message_history :]

    # 활동 시간 업데이트
    session.last_activity_at = datetime.utcnow()

    return session


def terminate_session(session_id: str) -> None:
    """
    세션 종료 (체크포인트 포함)

    Args:
        session_id: 세션 ID
    """
    if session_id in _sessions:
        _sessions[session_id].status = SessionStatus.TERMINATED
        # 체크포인트도 함께 삭제
        try:
            _checkpointer.delete_thread(session_id)
        except Exception as e:
            logger.warning(f"체크포인트 삭제 실패 ({session_id}): {e}")
        logger.info(f"세션 종료: {session_id}")


def reset_session(session_id: str) -> ConversationSession:
    """
    세션 초기화 (대화 맥락 리셋)

    Args:
        session_id: 세션 ID

    Returns:
        초기화된 세션
    """
    session = get_session(session_id)
    session.message_history = []
    session.last_activity_at = datetime.utcnow()
    logger.info(f"세션 초기화: {session_id}")
    return session


def get_or_create_session(
    session_id: str | None = None,
    llm_provider: str = "openai",
) -> ConversationSession:
    """
    세션 조회 또는 생성

    Args:
        session_id: 세션 ID (None이면 새 세션 생성)
        llm_provider: LLM 프로바이더 (새 세션 생성 시 사용)

    Returns:
        세션 정보
    """
    if session_id:
        try:
            return get_session(session_id)
        except (SessionNotFoundError, SessionExpiredError):
            logger.info(f"세션 {session_id} 없음/만료, 새 세션 생성")

    return create_session(llm_provider)


def _is_session_expired(session: ConversationSession) -> bool:
    """세션 만료 여부 확인"""
    settings = get_settings()
    timeout = timedelta(minutes=settings.session_timeout_minutes)
    return datetime.utcnow() - session.last_activity_at > timeout


def cleanup_expired_sessions() -> int:
    """
    만료된 세션 정리 (세션 데이터 + 체크포인트)

    Returns:
        정리된 세션 수
    """
    expired_ids = [
        sid
        for sid, session in _sessions.items()
        if _is_session_expired(session) or session.status != SessionStatus.ACTIVE
    ]

    for sid in expired_ids:
        del _sessions[sid]
        # InMemorySaver 체크포인트 정리 추가
        try:
            _checkpointer.delete_thread(sid)
        except Exception as e:
            logger.warning(f"체크포인트 삭제 실패 ({sid}): {e}")

    if expired_ids:
        logger.info(f"만료 세션 정리: {len(expired_ids)}개 (세션 + 체크포인트)")

    return len(expired_ids)
