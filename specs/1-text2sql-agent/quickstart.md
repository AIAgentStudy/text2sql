# Quickstart: Text2SQL Agent

## Prerequisites

- Python 3.11+
- PostgreSQL 15+ (with pgvector extension)
- Node.js 20+ (프론트엔드용)
- OpenAI API Key (기본 LLM)
- (Optional) Anthropic API Key, Google AI API Key

## 1. Environment Setup

```bash
# 프로젝트 클론 후 백엔드 설정
cd tsagent/backend

# 가상환경 생성 (권장)
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정
cp .env.example .env
```

`.env` 파일 설정:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/dbname

# LLM Providers
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...    # Optional
GOOGLE_AI_API_KEY=...           # Optional

# Server
HOST=0.0.0.0
PORT=8000
DEBUG=true

# Session
SESSION_TIMEOUT_MINUTES=30
```

## 2. Database Setup

PostgreSQL에 접속하여 필요한 권한을 설정합니다:

```sql
-- 읽기 전용 사용자 생성 (쿼리 실행용)
CREATE USER text2sql_readonly WITH PASSWORD 'your_password';
GRANT CONNECT ON DATABASE your_db TO text2sql_readonly;
GRANT USAGE ON SCHEMA public TO text2sql_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO text2sql_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO text2sql_readonly;

-- 테이블/컬럼 설명 추가 (한국어 지원)
COMMENT ON TABLE customers IS '고객 정보';
COMMENT ON COLUMN customers.name IS '고객 이름';
COMMENT ON COLUMN customers.created_at IS '가입일';
```

## 3. Run the Backend

```bash
# 개발 모드 (자동 리로드)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 또는 프로덕션 모드
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

서버가 시작되면:
- API: http://localhost:8000/api
- API 문서 (Swagger): http://localhost:8000/docs
- API 문서 (ReDoc): http://localhost:8000/redoc

## 4. Run the Frontend

```bash
cd ../frontend

# 의존성 설치
npm install

# 개발 서버 실행
npm run dev
```

프론트엔드 서버: http://localhost:5173

## 5. First Query

### Web UI 사용

1. 브라우저에서 http://localhost:5173 접속
2. 채팅창에 자연어로 질문 입력
   - 예: "지난달 매출 상위 10개 제품이 뭐야?"
3. 생성된 쿼리와 설명 확인
4. "실행" 버튼 클릭하여 결과 조회

### API 직접 호출

```bash
# 새 세션 시작 및 질문 (SSE 스트리밍)
curl -N -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{
    "message": "이번 달 신규 고객이 몇 명이야?"
  }'

# SSE 스트림 응답 예시:
# data: {"type":"session","session_id":"abc-123"}
# data: {"type":"status","status":"generating"}
# data: {"type":"query_preview","query":"SELECT COUNT(*) FROM customers WHERE created_at >= DATE_TRUNC('month', CURRENT_DATE)","explanation":"이번 달에 가입한 고객 수를 조회합니다."}
# data: {"type":"confirm_required","query_id":"query-456"}

# 쿼리 실행 승인
curl -X POST http://localhost:8000/api/chat/confirm \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "abc-123",
    "query_id": "query-456",
    "approved": true
  }'
```

### Python 클라이언트 예시

```python
import httpx
import json

async def ask_question(question: str, session_id: str | None = None):
    """Text2SQL Agent에 질문하기"""
    async with httpx.AsyncClient() as client:
        async with client.stream(
            "POST",
            "http://localhost:8000/api/chat",
            json={"message": question, "session_id": session_id},
            headers={"Accept": "text/event-stream"},
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    event = json.loads(line[6:])
                    print(f"Event: {event['type']}")

                    if event["type"] == "confirm_required":
                        # 자동 승인 (실제로는 사용자 입력 필요)
                        return event["query_id"], event.get("session_id")

# 사용 예시
import asyncio
asyncio.run(ask_question("지난달 매출 상위 10개 제품이 뭐야?"))
```

## 6. Example Queries

| 자연어 질문 | 생성되는 SQL |
|------------|-------------|
| "지난달 매출 상위 10개 제품" | `SELECT product_name, SUM(amount) FROM sales WHERE sale_date >= ... GROUP BY product_name ORDER BY 2 DESC LIMIT 10` |
| "서울 지역 고객 수" | `SELECT COUNT(*) FROM customers WHERE region = '서울'` |
| "최근 7일간 일별 주문 건수" | `SELECT DATE(order_date), COUNT(*) FROM orders WHERE order_date >= CURRENT_DATE - INTERVAL '7 days' GROUP BY 1 ORDER BY 1` |

## 7. Verification Checklist

- [ ] 서버 시작 확인: `curl http://localhost:8000/api/health`
- [ ] DB 연결 확인: health 응답에서 `database: ok`
- [ ] LLM 연결 확인: health 응답에서 `llm: ok`
- [ ] 간단한 쿼리 테스트: "테이블 목록 보여줘"
- [ ] 위험 쿼리 차단 확인: "모든 고객 정보 삭제해줘" → 거부 메시지

## 8. Troubleshooting

### "데이터베이스 연결 오류"

```bash
# PostgreSQL 실행 확인
pg_isready -h localhost -p 5432

# 연결 문자열 확인
psql $DATABASE_URL -c "SELECT 1"
```

### "LLM API 오류"

```bash
# OpenAI API 키 확인
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

### "쿼리 생성 실패"

- 질문이 너무 모호한 경우 → 더 구체적으로 질문
- 테이블/컬럼명이 없는 경우 → `/api/schema` 에서 스키마 확인
- 복잡한 질문 → 단순한 질문으로 나눠서 시도

## 9. Configuration Options

### LLM Provider 변경

```python
# 세션 생성 시 지정
POST /api/session
{
  "llm_provider": "anthropic"  # or "google"
}

# 또는 채팅 요청 시
POST /api/chat
{
  "message": "...",
  "llm_provider": "anthropic"
}
```

### 쿼리 제한 설정

환경 변수로 조정:

```env
QUERY_TIMEOUT_MS=30000        # 쿼리 타임아웃 (기본: 30초)
MAX_RESULT_ROWS=10000         # 최대 결과 행 수
DEFAULT_PAGE_SIZE=100         # 기본 페이지 크기
```

## 10. Development

### Type Checking

```bash
# mypy로 타입 체크
mypy src/

# 또는 pyright
pyright
```

### Linting & Formatting

```bash
# ruff로 린팅 및 포매팅
ruff check src/
ruff format src/
```

### Testing

```bash
# 전체 테스트 실행
pytest

# 커버리지 포함
pytest --cov=src --cov-report=html

# 특정 테스트만 실행
pytest tests/unit/test_validation.py -v
```
