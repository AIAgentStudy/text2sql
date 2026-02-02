"""
FastAPI 애플리케이션 엔트리포인트

Text2SQL Agent API 서버의 메인 진입점입니다.
"""

import logging
import time
import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.config import get_settings, setup_logging
from app.database.connection import close_pool, create_pool
from app.errors.handlers import register_error_handlers

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """요청 로깅 미들웨어"""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # 요청 ID 생성
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id

        # 요청 시작 시간
        start_time = time.perf_counter()

        # 요청 정보 로깅
        logger.info(
            f"[{request_id}] → {request.method} {request.url.path}"
            + (f"?{request.url.query}" if request.url.query else "")
        )

        # 요청 처리
        try:
            response = await call_next(request)
        except Exception as e:
            # 예외 발생 시 로깅
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.error(
                f"[{request_id}] ✗ {request.method} {request.url.path} "
                f"| 500 | {duration_ms:.1f}ms | {type(e).__name__}: {e}"
            )
            raise

        # 응답 시간 계산
        duration_ms = (time.perf_counter() - start_time) * 1000

        # 응답 로깅
        status_icon = "✓" if response.status_code < 400 else "✗"
        log_level = logging.WARNING if response.status_code >= 400 else logging.INFO
        logger.log(
            log_level,
            f"[{request_id}] {status_icon} {request.method} {request.url.path} "
            f"| {response.status_code} | {duration_ms:.1f}ms",
        )

        # 응답 헤더에 요청 ID 추가
        response.headers["X-Request-ID"] = request_id

        return response


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """애플리케이션 수명 주기 관리"""
    # 시작 시
    settings = get_settings()

    # 로깅 설정
    setup_logging(settings)

    logger.info("Text2SQL Agent 서버 시작 중...")

    # 데이터베이스 연결 풀 생성
    try:
        await create_pool(settings)
        logger.info("데이터베이스 연결 완료")
    except Exception as e:
        logger.error(f"데이터베이스 연결 실패: {e}")
        # 연결 실패해도 서버는 시작 (헬스체크에서 확인 가능)

    yield

    # 종료 시
    logger.info("Text2SQL Agent 서버 종료 중...")
    await close_pool()
    logger.info("서버 종료 완료")


def create_app() -> FastAPI:
    """FastAPI 애플리케이션 생성"""
    settings = get_settings()

    app = FastAPI(
        title="Text2SQL Agent API",
        description="자연어를 SQL 쿼리로 변환하고 실행하는 에이전트 API",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
    )

    # 요청 로깅 미들웨어 (먼저 등록)
    app.add_middleware(RequestLoggingMiddleware)

    # CORS 미들웨어 설정
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 에러 핸들러 등록
    register_error_handlers(app)

    # 라우터 등록
    from app.api.routes import auth, chat, graph, health, schema, session

    app.include_router(health.router, prefix="/api", tags=["Health"])
    app.include_router(auth.router, prefix="/api", tags=["Auth"])
    app.include_router(chat.router, prefix="/api", tags=["Chat"])
    app.include_router(session.router, prefix="/api", tags=["Session"])
    app.include_router(schema.router, prefix="/api", tags=["Schema"])
    app.include_router(graph.router, prefix="/api", tags=["Graph"])

    return app


# 애플리케이션 인스턴스
app = create_app()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
