"""
애플리케이션 설정 관리

Pydantic Settings를 사용하여 환경 변수에서 설정을 로드합니다.
"""

import logging
import sys
from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """애플리케이션 설정"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # === 서버 설정 ===
    host: str = Field(default="0.0.0.0", description="서버 호스트")
    port: int = Field(default=8000, description="서버 포트")
    debug: bool = Field(default=False, description="디버그 모드")

    # === 데이터베이스 설정 ===
    database_url: PostgresDsn = Field(
        ...,
        description="PostgreSQL 연결 문자열",
    )
    db_pool_min_size: int = Field(default=5, description="DB 연결 풀 최소 크기")
    db_pool_max_size: int = Field(default=20, description="DB 연결 풀 최대 크기")

    # === LLM API 키 ===
    openai_api_key: str | None = Field(default=None, description="OpenAI API 키")
    anthropic_api_key: str | None = Field(default=None, description="Anthropic API 키")
    google_ai_api_key: str | None = Field(default=None, description="Google AI API 키")

    # === LLM 설정 ===
    default_llm_provider: Literal["openai", "anthropic", "google"] = Field(
        default="openai",
        description="기본 LLM 제공자",
    )
    llm_temperature: float = Field(default=0.0, description="LLM 온도 설정")
    llm_max_tokens: int = Field(default=2048, description="LLM 최대 토큰 수")

    # === 세션 설정 ===
    session_timeout_minutes: int = Field(default=30, description="세션 타임아웃 (분)")
    max_message_history: int = Field(default=10, description="최대 메시지 히스토리 수")

    # === 쿼리 제한 설정 ===
    query_timeout_ms: int = Field(default=30000, description="쿼리 타임아웃 (밀리초)")
    max_result_rows: int = Field(default=10000, description="최대 결과 행 수")
    default_page_size: int = Field(default=100, description="기본 페이지 크기")
    max_generation_attempts: int = Field(default=3, description="쿼리 생성 최대 시도 횟수")

    # === Human-in-the-Loop 설정 ===
    auto_confirm_queries: bool = Field(
        default=True,
        description="쿼리 자동 확인 모드 (False면 사용자 확인 필요)",
    )
    require_confirmation_for_large_results: bool = Field(
        default=False,
        description="대용량 결과 예상 시 확인 필요 여부",
    )

    # === 로깅 설정 ===
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="로그 레벨",
    )

    # === CORS 설정 ===
    cors_origins: list[str] = Field(
        default=["http://localhost:5173", "http://localhost:3000"],
        description="허용된 CORS 오리진",
    )

    @property
    def database_url_str(self) -> str:
        """데이터베이스 URL을 문자열로 반환"""
        return str(self.database_url)


@lru_cache
def get_settings() -> Settings:
    """설정 인스턴스를 가져옵니다 (캐싱됨)"""
    return Settings()


def setup_logging(settings: Settings | None = None) -> None:
    """
    구조화된 로깅 설정

    Args:
        settings: 애플리케이션 설정 (없으면 자동 로드)
    """
    if settings is None:
        settings = get_settings()

    # 로그 포맷 설정
    log_format = (
        "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s"
        if settings.debug
        else "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    )

    # JSON 포맷 (프로덕션용)
    json_format = (
        '{"time": "%(asctime)s", "level": "%(levelname)s", '
        '"logger": "%(name)s", "message": "%(message)s"}'
    )

    # 핸들러 설정
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            log_format if settings.debug else json_format,
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )

    # 루트 로거 설정
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.log_level))
    root_logger.handlers = [handler]

    # 서드파티 라이브러리 로그 레벨 조정
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("asyncpg").setLevel(logging.WARNING)

    logging.info(f"로깅 설정 완료: 레벨={settings.log_level}, 디버그={settings.debug}")
