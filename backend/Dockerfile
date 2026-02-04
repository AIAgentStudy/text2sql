FROM python:3.11-slim AS base

# 환경 변수 설정
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 의존성 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# -------------------------------------------
# Builder 스테이지: 의존성 설치
# -------------------------------------------
FROM base AS builder

# 의존성 파일 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# -------------------------------------------
# Production 스테이지: 최종 이미지
# -------------------------------------------
FROM base AS production

# 빌더에서 설치된 패키지 복사
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# 애플리케이션 코드 복사
COPY src/ ./src/

# Alembic 마이그레이션 파일 복사
COPY alembic.ini ./
COPY migrations/ ./migrations/
COPY entrypoint.sh ./

# Python 경로 설정
ENV PYTHONPATH=/app/src

# 비루트 사용자 생성, 스크립트 권한 설정
# Windows에서 작성된 스크립트의 CRLF 문제를 방지하기 위해 sed 명령어로 변환
RUN useradd --create-home --shell /bin/bash appuser && \
    chmod +x entrypoint.sh && \
    sed -i 's/\r$//' entrypoint.sh && \
    chown -R appuser:appuser /app

USER appuser

# 포트 노출
EXPOSE 8000

# 서버 실행 (entrypoint.sh를 통해 마이그레이션 후 실행)
CMD ["./entrypoint.sh"]
