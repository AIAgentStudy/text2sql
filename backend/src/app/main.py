"""
FastAPI 애플리케이션 엔트리포인트

Text2SQL Agent API 서버의 메인 진입점입니다.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database.connection import close_pool, create_pool
from app.errors.handlers import register_error_handlers

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """애플리케이션 수명 주기 관리"""
    # 시작 시
    logger.info("Text2SQL Agent 서버 시작 중...")
    settings = get_settings()

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

    # CORS 미들웨어 설정
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 에러 핸들러 등록
    register_error_handlers(app)

    # 라우터 등록
    from app.api.routes import chat, health

    app.include_router(health.router, prefix="/api", tags=["Health"])
    app.include_router(chat.router, prefix="/api", tags=["Chat"])

    # 추가 라우터는 여기에 등록 (US3 이후)
    # from app.api.routes import session, schema
    # app.include_router(session.router, prefix="/api", tags=["Session"])
    # app.include_router(schema.router, prefix="/api", tags=["Schema"])

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
