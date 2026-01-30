"""
OpenAI LLM 프로바이더

GPT-4o 및 GPT-4o-mini 모델을 지원합니다.
"""

import logging

from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI

from app.config import get_settings
from app.errors.exceptions import LLMError
from app.llm.base import DEFAULT_MODELS, LLMConfig

logger = logging.getLogger(__name__)


class OpenAIProvider:
    """OpenAI LLM 프로바이더"""

    @property
    def provider_name(self) -> str:
        return "openai"

    def _get_api_key(self) -> str:
        """API 키 반환"""
        settings = get_settings()
        if not settings.openai_api_key:
            raise LLMError("openai", "OPENAI_API_KEY가 설정되지 않았습니다.")
        return settings.openai_api_key

    def get_chat_model(self, config: LLMConfig | None = None) -> BaseChatModel:
        """채팅 모델 인스턴스 반환 (GPT-4o)"""
        api_key = self._get_api_key()
        settings = get_settings()

        model_name = (
            config.model_name if config else DEFAULT_MODELS["openai"]["chat"]
        )
        temperature = config.temperature if config else settings.llm_temperature
        max_tokens = config.max_tokens if config else settings.llm_max_tokens

        return ChatOpenAI(
            model=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=api_key,
        )

    def get_fast_model(self, config: LLMConfig | None = None) -> BaseChatModel:
        """빠른 모델 인스턴스 반환 (GPT-4o-mini, 검증용)"""
        api_key = self._get_api_key()
        settings = get_settings()

        model_name = (
            config.model_name if config else DEFAULT_MODELS["openai"]["fast"]
        )
        temperature = config.temperature if config else 0.0

        return ChatOpenAI(
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
            logger.warning(f"OpenAI API 확인 실패: {e}")
            return False
