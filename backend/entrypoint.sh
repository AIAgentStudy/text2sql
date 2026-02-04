#!/bin/bash
set -e

# 데이터베이스 접속 대기 (선택 사항, 필요 시 주석 해제하여 사용)
# ./wait-for-it.sh db:5432 --timeout=30 --strict -- echo "Database is up"

# 마이그레이션 실행
echo "Running database migrations..."
alembic upgrade head

# 서버 실행
echo "Starting server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
