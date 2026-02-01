"""
스키마 조회 API 엔드포인트

데이터베이스 스키마 정보를 조회하고 갱신하는 API입니다.
"""

import logging

from fastapi import APIRouter, HTTPException, status

from app.database.schema import clear_schema_cache, get_database_schema
from app.errors.exceptions import DatabaseConnectionError
from app.models.responses import DatabaseSchemaResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/schema")


@router.get(
    "",
    response_model=DatabaseSchemaResponse,
    summary="스키마 조회",
    description="데이터베이스 스키마 정보를 조회합니다. 캐시된 정보를 반환합니다.",
)
async def get_schema() -> DatabaseSchemaResponse:
    """
    데이터베이스 스키마 조회

    Returns:
        DatabaseSchemaResponse: 스키마 정보 (테이블, 컬럼 등)

    Raises:
        HTTPException: 데이터베이스 연결 실패 시
    """
    try:
        schema = await get_database_schema(force_refresh=False)
    except DatabaseConnectionError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": "DATABASE_CONNECTION_ERROR",
                "message": "현재 데이터베이스에 연결할 수 없습니다.",
            },
        )
    except Exception as e:
        logger.error(f"스키마 조회 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "SCHEMA_FETCH_ERROR",
                "message": "스키마 정보를 가져오는 중 오류가 발생했습니다.",
            },
        )

    return DatabaseSchemaResponse(
        version=schema.version,
        last_updated_at=schema.last_updated_at,
        tables=schema.tables,
    )


@router.post(
    "/refresh",
    response_model=DatabaseSchemaResponse,
    summary="스키마 갱신",
    description="스키마 캐시를 무효화하고 최신 정보를 다시 조회합니다.",
)
async def refresh_schema() -> DatabaseSchemaResponse:
    """
    스키마 캐시 갱신

    캐시를 무효화하고 데이터베이스에서 최신 스키마를 다시 조회합니다.

    Returns:
        DatabaseSchemaResponse: 최신 스키마 정보

    Raises:
        HTTPException: 데이터베이스 연결 실패 시
    """
    try:
        # 캐시 초기화
        clear_schema_cache()

        # 새로 조회
        schema = await get_database_schema(force_refresh=True)
        logger.info(f"스키마 갱신 완료: 버전 {schema.version}")

    except DatabaseConnectionError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": "DATABASE_CONNECTION_ERROR",
                "message": "현재 데이터베이스에 연결할 수 없습니다.",
            },
        )
    except Exception as e:
        logger.error(f"스키마 갱신 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "SCHEMA_REFRESH_ERROR",
                "message": "스키마를 갱신하는 중 오류가 발생했습니다.",
            },
        )

    return DatabaseSchemaResponse(
        version=schema.version,
        last_updated_at=schema.last_updated_at,
        tables=schema.tables,
    )
