"""
API 요청 모델 정의

OpenAPI 계약(contracts/api.yaml)에 정의된 요청 스키마들입니다.
"""

from typing import Literal

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """채팅 요청"""

    session_id: str | None = Field(
        default=None,
        description="기존 세션 ID (없으면 새 세션 생성)",
    )
    message: str = Field(
        min_length=2,
        max_length=1000,
        description="사용자의 자연어 질문",
        examples=["지난달 매출 상위 10개 제품이 뭐야?"],
    )
    llm_provider: Literal["openai", "anthropic", "google"] = Field(
        default="openai",
        description="사용할 LLM 제공자",
    )


class ConfirmationRequest(BaseModel):
    """쿼리 실행 확인 요청"""

    session_id: str = Field(description="세션 ID")
    query_id: str = Field(description="확인할 쿼리 ID")
    approved: bool = Field(description="true=실행 승인, false=취소")


class CreateSessionRequest(BaseModel):
    """세션 생성 요청"""

    llm_provider: Literal["openai", "anthropic", "google"] = Field(
        default="openai",
        description="사용할 LLM 제공자",
    )
