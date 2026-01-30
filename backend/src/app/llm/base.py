"""
LLM 프로바이더 기본 인터페이스

Protocol을 사용하여 타입 안전한 추상화를 제공합니다.
"""

from typing import Literal, Protocol

from langchain_core.language_models import BaseChatModel
from pydantic import BaseModel


class LLMConfig(BaseModel):
    """LLM 설정"""

    provider: Literal["openai", "anthropic", "google"]
    model_name: str
    temperature: float = 0.0
    max_tokens: int = 2048


class LLMProvider(Protocol):
    """LLM 프로바이더 프로토콜"""

    @property
    def provider_name(self) -> str:
        """프로바이더 이름"""
        ...

    def get_chat_model(self, config: LLMConfig) -> BaseChatModel:
        """채팅 모델 인스턴스 반환"""
        ...

    def get_fast_model(self, config: LLMConfig) -> BaseChatModel:
        """빠른 모델 인스턴스 반환 (검증용)"""
        ...

    async def check_availability(self) -> bool:
        """API 가용성 확인"""
        ...


# 기본 모델 설정
DEFAULT_MODELS = {
    "openai": {
        "chat": "gpt-4o",
        "fast": "gpt-4o-mini",
    },
    "anthropic": {
        "chat": "claude-3-5-sonnet-latest",
        "fast": "claude-3-5-haiku-latest",
    },
    "google": {
        "chat": "gemini-1.5-pro",
        "fast": "gemini-1.5-flash",
    },
}
