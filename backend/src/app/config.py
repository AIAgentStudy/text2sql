"""
애플리케이션 설정 관리

Pydantic Settings를 사용하여 환경 변수에서 설정을 로드합니다.
"""

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

    # === 검증 설정 ===
    enable_semantic_validation: bool = Field(
        default=True,
        description="LLM 시맨틱 검증 활성화 여부",
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
