"""
LLM 프로바이더 팩토리

런타임에 LLM 프로바이더를 선택하고 인스턴스를 생성합니다.
"""

import logging
from typing import Literal

from langchain_core.language_models import BaseChatModel

from app.config import get_settings
from app.errors.exceptions import LLMError
from app.llm.anthropic import AnthropicProvider
from app.llm.base import LLMConfig
from app.llm.google import GoogleProvider
from app.llm.openai import OpenAIProvider

logger = logging.getLogger(__name__)

ProviderType = Literal["openai", "anthropic", "google"]

# 프로바이더 인스턴스 캐시
_providers: dict[ProviderType, OpenAIProvider | AnthropicProvider | GoogleProvider] = {}


def get_provider(
    provider_type: ProviderType | None = None,
) -> OpenAIProvider | AnthropicProvider | GoogleProvider:
    """
    LLM 프로바이더 인스턴스 반환

    Args:
        provider_type: 프로바이더 타입 (None이면 기본 설정 사용)

    Returns:
        LLM 프로바이더 인스턴스
    """
    if provider_type is None:
        settings = get_settings()
        provider_type = settings.default_llm_provider

    if provider_type not in _providers:
        match provider_type:
            case "openai":
                _providers[provider_type] = OpenAIProvider()
            case "anthropic":
                _providers[provider_type] = AnthropicProvider()
            case "google":
                _providers[provider_type] = GoogleProvider()
            case _:
                raise LLMError(provider_type, f"지원하지 않는 프로바이더: {provider_type}")

    return _providers[provider_type]


def get_chat_model(
    provider_type: ProviderType | None = None,
    config: LLMConfig | None = None,
) -> BaseChatModel:
    """
    채팅 모델 인스턴스 반환

    Args:
        provider_type: 프로바이더 타입 (None이면 기본 설정 사용)
        config: LLM 설정 (None이면 기본 설정 사용)

    Returns:
        BaseChatModel 인스턴스
    """
    provider = get_provider(provider_type)
    return provider.get_chat_model(config)


def get_fast_model(
    provider_type: ProviderType | None = None,
    config: LLMConfig | None = None,
) -> BaseChatModel:
    """
    빠른 모델 인스턴스 반환 (검증용)

    Args:
        provider_type: 프로바이더 타입 (None이면 기본 설정 사용)
        config: LLM 설정 (None이면 기본 설정 사용)

    Returns:
        BaseChatModel 인스턴스
    """
    provider = get_provider(provider_type)
    return provider.get_fast_model(config)


async def check_llm_availability(
    provider_type: ProviderType | None = None,
) -> bool:
    """
    LLM API 가용성 확인

    Args:
        provider_type: 프로바이더 타입 (None이면 기본 설정 사용)

    Returns:
        True if available, False otherwise
    """
    try:
        provider = get_provider(provider_type)
        return await provider.check_availability()
    except LLMError:
        return False
    except Exception as e:
        logger.warning(f"LLM 가용성 확인 중 오류: {e}")
        return False
