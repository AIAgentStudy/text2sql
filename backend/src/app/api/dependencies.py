"""
FastAPI 의존성

API 엔드포인트에서 사용하는 공통 의존성을 정의합니다.
"""

import logging
from typing import Annotated

import asyncpg
from fastapi import Depends
from langchain_core.language_models import BaseChatModel
from langgraph.checkpoint.memory import InMemorySaver

from app.config import Settings, get_settings
from app.database.connection import get_pool
from app.llm.factory import ProviderType, get_chat_model
from app.session.manager import get_checkpointer

logger = logging.getLogger(__name__)


def get_db_pool() -> asyncpg.Pool:
    """
    데이터베이스 연결 풀 의존성

    Returns:
        asyncpg.Pool: 연결 풀
    """
    return get_pool()


def get_llm(
    provider: ProviderType | None = None,
) -> BaseChatModel:
    """
    LLM 모델 의존성

    Args:
        provider: LLM 프로바이더 타입

    Returns:
        BaseChatModel: LLM 모델 인스턴스
    """
    return get_chat_model(provider)


def get_session_checkpointer() -> InMemorySaver:
    """
    세션 체크포인터 의존성

    Returns:
        InMemorySaver: LangGraph 체크포인터
    """
    return get_checkpointer()


# 타입 별칭
SettingsDep = Annotated[Settings, Depends(get_settings)]
DBPoolDep = Annotated[asyncpg.Pool, Depends(get_db_pool)]
CheckpointerDep = Annotated[InMemorySaver, Depends(get_session_checkpointer)]


def get_llm_for_provider(provider: ProviderType) -> BaseChatModel:
    """
    특정 프로바이더의 LLM 모델 반환

    Args:
        provider: LLM 프로바이더 타입

    Returns:
        BaseChatModel: LLM 모델 인스턴스
    """
    return get_chat_model(provider)
