"""
헬스 체크 엔드포인트

서비스 및 의존성 상태를 확인합니다.
"""

import logging
from datetime import datetime
from typing import Literal

from fastapi import APIRouter

from app.database.connection import check_connection
from app.llm.factory import check_llm_availability
from app.models.responses import HealthDependencies, HealthResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="헬스 체크",
    description="서비스 및 의존성 상태를 확인합니다.",
)
async def health_check() -> HealthResponse:
    """
    서비스 헬스 체크

    데이터베이스 및 LLM API 연결 상태를 확인하고 전체 상태를 반환합니다.
    """
    # 데이터베이스 연결 확인
    db_status: Literal["ok", "error"] = "ok" if await check_connection() else "error"

    # LLM API 연결 확인
    llm_status: Literal["ok", "error"] = "ok" if await check_llm_availability() else "error"

    # 전체 상태 결정
    if db_status == "ok" and llm_status == "ok":
        status: Literal["healthy", "degraded", "unhealthy"] = "healthy"
    elif db_status == "error" and llm_status == "error":
        status = "unhealthy"
    else:
        status = "degraded"

    return HealthResponse(
        status=status,
        timestamp=datetime.utcnow(),
        dependencies=HealthDependencies(
            database=db_status,
            llm=llm_status,
        ),
    )


@router.get(
    "/health/live",
    summary="라이브니스 체크",
    description="서버가 실행 중인지 확인합니다.",
)
async def liveness_check() -> dict[str, str]:
    """
    라이브니스 체크 (Kubernetes용)

    서버가 실행 중인지만 확인합니다 (의존성 확인 없음).
    """
    return {"status": "alive"}


@router.get(
    "/health/ready",
    summary="레디니스 체크",
    description="서버가 요청을 처리할 준비가 되었는지 확인합니다.",
)
async def readiness_check() -> dict[str, str]:
    """
    레디니스 체크 (Kubernetes용)

    데이터베이스 연결이 되어있는지 확인합니다.
    """
    if await check_connection():
        return {"status": "ready"}
    return {"status": "not_ready"}
