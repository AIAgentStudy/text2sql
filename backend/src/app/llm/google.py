"""
Google LLM 프로바이더

Gemini 2.5 Flash 및 Flash-Lite 모델을 지원합니다.
"""

import logging

from langchain_core.language_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI

from app.config import get_settings
from app.errors.exceptions import LLMError
from app.llm.base import DEFAULT_MODELS, LLMConfig

logger = logging.getLogger(__name__)


class GoogleProvider:
    """Google LLM 프로바이더"""

    @property
    def provider_name(self) -> str:
        return "google"

    def _get_api_key(self) -> str:
        """API 키 반환"""
        settings = get_settings()
        if not settings.google_ai_api_key:
            raise LLMError("google", "GOOGLE_AI_API_KEY가 설정되지 않았습니다.")
        return settings.google_ai_api_key

    def get_chat_model(self, config: LLMConfig | None = None) -> BaseChatModel:
        """채팅 모델 인스턴스 반환 (Gemini 2.5 Flash)"""
        api_key = self._get_api_key()
        settings = get_settings()

        model_name = (
            config.model_name if config else DEFAULT_MODELS["google"]["chat"]
        )
        temperature = config.temperature if config else settings.llm_temperature
        max_tokens = config.max_tokens if config else settings.llm_max_tokens

        return ChatGoogleGenerativeAI(
            model=model_name,
            temperature=temperature,
            max_output_tokens=max_tokens,
            google_api_key=api_key,
        )

    def get_fast_model(self, config: LLMConfig | None = None) -> BaseChatModel:
        """빠른 모델 인스턴스 반환 (Gemini 2.5 Flash-Lite, 검증용)"""
        api_key = self._get_api_key()

        model_name = (
            config.model_name if config else DEFAULT_MODELS["google"]["fast"]
        )
        temperature = config.temperature if config else 0.0

        return ChatGoogleGenerativeAI(
            model=model_name,
            temperature=temperature,
            max_output_tokens=1024,
            google_api_key=api_key,
        )

    async def check_availability(self) -> bool:
        """API 가용성 확인"""
        try:
            model = self.get_fast_model()
            response = await model.ainvoke("Hi")
            return response.content is not None
        except Exception as e:
            logger.warning(f"Google AI API 확인 실패: {e}")
            return False
