"""
헬스 체크 엔드포인트

서비스 및 의존성 상태를 확인합니다.
"""

import logging
from datetime import datetime
from typing import Literal

from fastapi import APIRouter

from app.database.connection import check_connection
from app.models.responses import HealthDependencies, HealthResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="헬스 체크",
    description="서비스 및 데이터베이스 상태를 확인합니다.",
)
async def health_check() -> HealthResponse:
    """
    서비스 헬스 체크

    데이터베이스 연결 상태를 확인하고 전체 상태를 반환합니다.
    """
    # 데이터베이스 연결 확인
    db_status: Literal["ok", "error"] = "ok" if await check_connection() else "error"

    # 전체 상태 결정
    status: Literal["healthy", "unhealthy"] = "healthy" if db_status == "ok" else "unhealthy"

    return HealthResponse(
        status=status,
        timestamp=datetime.utcnow(),
        dependencies=HealthDependencies(
            database=db_status,
        ),
    )
