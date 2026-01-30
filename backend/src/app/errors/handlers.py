"""
FastAPI 에러 핸들러

전역 예외 처리를 담당합니다.
"""

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.errors.exceptions import Text2SQLError
from app.models.responses import ErrorDetail, ErrorResponse

logger = logging.getLogger(__name__)


def create_error_response(code: str, message: str) -> dict[str, Any]:
    """에러 응답 생성"""
    return ErrorResponse(error=ErrorDetail(code=code, message=message)).model_dump()


async def text2sql_error_handler(request: Request, exc: Text2SQLError) -> JSONResponse:
    """Text2SQL 커스텀 예외 처리"""
    # 심각도에 따른 로깅
    if exc.severity == "security":
        logger.warning(f"보안 관련 오류: {exc.code} - {exc}")
    elif exc.severity == "system":
        logger.error(f"시스템 오류: {exc.code} - {exc}")
    else:
        logger.info(f"사용자 오류: {exc.code} - {exc}")

    # 심각도에 따른 HTTP 상태 코드
    status_code_map = {
        "security": 403,
        "system": 500,
        "user": 400,
    }
    status_code = status_code_map.get(exc.severity, 400)

    return JSONResponse(
        status_code=status_code,
        content=create_error_response(exc.code, exc.user_message),
    )


async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """일반 예외 처리"""
    logger.exception(f"예상치 못한 오류 발생: {exc}")

    return JSONResponse(
        status_code=500,
        content=create_error_response(
            "INTERNAL_ERROR",
            "서버에서 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
        ),
    )


def register_error_handlers(app: FastAPI) -> None:
    """FastAPI 앱에 에러 핸들러 등록"""
    app.add_exception_handler(Text2SQLError, text2sql_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, generic_error_handler)
