"""
Anthropic LLM 프로바이더

Claude 3.5 Sonnet 및 Haiku 모델을 지원합니다.
"""

import logging

from langchain_anthropic import ChatAnthropic
from langchain_core.language_models import BaseChatModel

from app.config import get_settings
from app.errors.exceptions import LLMError
from app.llm.base import DEFAULT_MODELS, LLMConfig

logger = logging.getLogger(__name__)


class AnthropicProvider:
    """Anthropic LLM 프로바이더"""

    @property
    def provider_name(self) -> str:
        return "anthropic"

    def _get_api_key(self) -> str:
        """API 키 반환"""
        settings = get_settings()
        if not settings.anthropic_api_key:
            raise LLMError("anthropic", "ANTHROPIC_API_KEY가 설정되지 않았습니다.")
        return settings.anthropic_api_key

    def get_chat_model(self, config: LLMConfig | None = None) -> BaseChatModel:
        """채팅 모델 인스턴스 반환 (Claude 3.5 Sonnet)"""
        api_key = self._get_api_key()
        settings = get_settings()

        model_name = (
            config.model_name if config else DEFAULT_MODELS["anthropic"]["chat"]
        )
        temperature = config.temperature if config else settings.llm_temperature
        max_tokens = config.max_tokens if config else settings.llm_max_tokens

        return ChatAnthropic(
            model=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=api_key,
        )

    def get_fast_model(self, config: LLMConfig | None = None) -> BaseChatModel:
        """빠른 모델 인스턴스 반환 (Claude 3.5 Haiku, 검증용)"""
        api_key = self._get_api_key()

        model_name = (
            config.model_name if config else DEFAULT_MODELS["anthropic"]["fast"]
        )
        temperature = config.temperature if config else 0.0

        return ChatAnthropic(
            model=model_name,
            temperature=temperature,
            max_tokens=1024,
            api_key=api_key,
        )

    async def check_availability(self) -> bool:
        """API 가용성 확인"""
        try:
            model = self.get_fast_model()
            response = await model.ainvoke("Hi")
            return response.content is not None
        except Exception as e:
            logger.warning(f"Anthropic API 확인 실패: {e}")
            return False
