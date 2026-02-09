# Text2SQL Agent - Backend

LangGraph 기반 AI 에이전트를 활용한 자연어-SQL 변환 API 서버입니다.

## 개요

FastAPI로 구축된 비동기 API 서버로, LangGraph 워크플로우를 통해 자연어 질문을 안전한 SQL 쿼리로 변환하고 실행합니다.

## 기술 스택

- **Python 3.11+**
- **FastAPI** - 비동기 웹 프레임워크
- **LangGraph 1.0+** - AI 에이전트 워크플로우
- **LangChain 1.2+** - LLM 통합
- **asyncpg** - 비동기 PostgreSQL 드라이버
- **Pydantic** - 데이터 검증
- **SSE-Starlette** - Server-Sent Events 지원
- **sqlglot** - SQL 파싱 및 테이블 추출

## 프로젝트 구조

```
backend/
├── src/app/
│   ├── agent/              # LangGraph 에이전트
│   │   ├── graph.py        # 워크플로우 정의
│   │   ├── state.py        # 에이전트 상태
│   │   └── nodes/          # 워크플로우 노드
│   │       ├── schema_retrieval.py
│   │       ├── permission_pre_check.py
│   │       ├── query_generation.py
│   │       ├── query_validation.py
│   │       ├── user_confirmation.py
│   │       ├── query_execution.py
│   │       └── response_formatting.py
│   ├── api/                # FastAPI 라우터
│   │   ├── routes/
│   │   │   ├── auth.py     # 인증 엔드포인트
│   │   │   ├── chat.py     # 채팅 엔드포인트
│   │   │   ├── session.py  # 세션 관리
│   │   │   ├── schema.py   # 스키마 조회
│   │   │   └── health.py   # 헬스체크
│   │   └── dependencies.py # FastAPI 의존성
│   ├── database/           # 데이터베이스
│   │   ├── connection.py   # 연결 풀 관리
│   │   ├── schema.py       # 스키마 추출
│   │   └── executor.py     # 쿼리 실행기
│   ├── llm/                # LLM 프로바이더
│   │   ├── base.py         # 프로토콜 정의
│   │   ├── factory.py      # 팩토리 패턴
│   │   ├── openai.py
│   │   ├── anthropic.py
│   │   └── google.py
│   ├── validation/         # 쿼리 검증
│   │   ├── keyword_validator.py   # 1단계: 키워드
│   │   ├── schema_validator.py    # 2단계: 스키마
│   │   └── semantic_validator.py  # 3단계: 시맨틱
│   ├── session/            # 세션 관리
│   │   └── manager.py
│   ├── models/             # Pydantic 모델
│   │   ├── entities.py
│   │   ├── requests.py
│   │   └── responses.py
│   ├── errors/             # 에러 처리
│   │   ├── exceptions.py
│   │   ├── handlers.py
│   │   └── messages.py
│   ├── config.py           # 설정 관리
│   └── main.py             # 엔트리포인트
├── tests/                  # 테스트
│   ├── unit/
│   ├── integration/
│   └── contract/
├── Dockerfile
├── requirements.txt
└── pyproject.toml
```

## 설치 및 실행

### 요구사항

- Python 3.11+
- PostgreSQL 15+
- OpenAI API 키 (또는 다른 LLM 제공자)

### 로컬 개발

```bash
# 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정
export DATABASE_URL=postgresql://user:pass@localhost:5432/dbname
export OPENAI_API_KEY=your-api-key
export DEBUG=true

# 서버 실행
python -m app.main

# 또는 uvicorn으로 직접 실행
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Docker

```bash
# 이미지 빌드
docker build -t text2sql-backend .

# 컨테이너 실행
docker run -p 8000:8000 \
  -e DATABASE_URL=postgresql://user:pass@host:5432/db \
  -e OPENAI_API_KEY=your-key \
  text2sql-backend
```

## API 엔드포인트

### 인증

| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/api/auth/register` | 회원가입 |
| POST | `/api/auth/login` | 로그인 |
| POST | `/api/auth/logout` | 로그아웃 |
| POST | `/api/auth/refresh` | 토큰 갱신 |
| GET | `/api/auth/me` | 현재 사용자 정보 |

### 채팅

#### POST /api/chat
자연어 질문을 처리하고 SQL 쿼리를 생성/실행합니다.

**Request:**
```json
{
  "session_id": "optional-session-id",
  "message": "지난달 매출 상위 10개 제품이 뭐야?",
  "llm_provider": "openai"
}
```

**Response:** Server-Sent Events (SSE) 스트림
```
data: {"type": "session", "session_id": "uuid"}
data: {"type": "status", "status": "generating", "message": "SQL 쿼리 생성 중..."}
data: {"type": "query_preview", "query": "SELECT ...", "explanation": "지난달 매출 상위 10개 제품을 조회합니다."}
data: {"type": "confirmation_required", "query_id": "uuid", "query": "...", "explanation": "..."}
data: {"type": "result", "data": {"rows": [...], "total_row_count": 10}}
data: {"type": "done", "awaiting_confirmation": false}
```

#### POST /api/chat/confirm
쿼리 실행을 확인하거나 취소합니다.

**Request:**
```json
{
  "session_id": "session-id",
  "query_id": "query-id",
  "approved": true
}
```

### 세션

| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/api/sessions` | 새 세션 생성 |
| GET | `/api/sessions/{id}` | 세션 조회 |
| DELETE | `/api/sessions/{id}` | 세션 종료 |

### 스키마

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/schema` | DB 스키마 조회 |
| POST | `/api/schema/refresh` | 스키마 캐시 갱신 |

### 헬스체크

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/health` | 서버 상태 확인 |

## 에이전트 워크플로우

```
┌─────────────────┐
│  Permission     │ 사전 권한 검증
│  Pre-check      │ (접근 불가 테이블 조기 차단)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Schema         │ 데이터베이스 스키마 조회
│  Retrieval      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Query          │ LLM으로 SQL 쿼리 생성
│  Generation     │ (최대 3회 재시도)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Query          │ 3단계 검증
│  Validation     │ (키워드 → 스키마 → 시맨틱)
└────────┬────────┘
         │
    ┌────┴────┐
    │ 검증    │
    │ 실패?   │──Yes──▶ 재생성 (최대 3회)
    └────┬────┘
         │ No
         ▼
┌─────────────────┐
│  User           │ 사용자 확인 대기
│  Confirmation   │ (Human-in-the-Loop)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Query          │ READ ONLY로 쿼리 실행
│  Execution      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Response       │ 결과 포맷팅
│  Formatting     │
└─────────────────┘
```

### 노드 상세 설명

#### 1. Permission Pre-check (권한 사전 검증)
**파일**: `agent/nodes/permission_pre_check.py`

Fail-Fast 패턴을 적용하여 권한 없는 요청을 워크플로우 초기에 차단합니다.
- 사용자 역할(roles)에 따라 접근 가능한 테이블 목록 조회
- 빠른 LLM 모델로 질문에서 필요한 테이블 추론
- 접근 불가 테이블이 포함된 경우 즉시 에러 반환 (LLM 비용 절감)

#### 2. Schema Retrieval (스키마 조회)
**파일**: `agent/nodes/schema_retrieval.py`

데이터베이스 스키마를 조회하고 권한 기반 필터링을 수행합니다.
- PostgreSQL information_schema에서 테이블/컬럼 메타데이터 조회
- 사용자 접근 가능 테이블만 포함하도록 필터링
- LLM 프롬프트에 적합한 형식으로 스키마 포맷팅

#### 3. Query Generation (쿼리 생성)
**파일**: `agent/nodes/query_generation.py`

LLM을 활용하여 자연어 질문을 SQL SELECT 쿼리로 변환합니다.
- Few-shot 예시를 통한 일관된 쿼리 스타일 유도
- 대화 맥락 참조 감지 ("그중에", "이전 결과에서" 등)
- 맥락 인식 모드로 연속 질문 처리 지원
- 모호한 질문 감지 및 명확화 요청

#### 4. Query Validation (쿼리 검증)
**파일**: `agent/nodes/query_validation.py`

생성된 쿼리를 3단계 검증 파이프라인으로 검사합니다.
- **1단계 키워드 검증**: 위험 키워드(UPDATE, DELETE 등) 패턴 매칭
- **2단계 스키마 검증**: 참조된 테이블/컬럼 존재 여부 확인
- **3단계 시맨틱 검증**: LLM으로 의도 분석 및 우회 시도 탐지
- 검증 실패 시 힌트와 함께 재생성 트리거 (최대 3회)

#### 5. User Confirmation (사용자 확인)
**파일**: `agent/nodes/user_confirmation.py`

Human-in-the-Loop 패턴으로 쿼리 실행 전 사용자 승인을 받습니다.
- LangGraph `interrupt()` 함수로 워크플로우 일시 중단
- 쿼리 미리보기와 설명을 프론트엔드에 전송
- 사용자 승인/거부에 따라 `Command(resume)` 으로 워크플로우 재개

#### 6. Query Execution (쿼리 실행)
**파일**: `agent/nodes/query_execution.py`

검증된 쿼리를 안전하게 실행합니다.
- 최종 권한 검증 (Defense-in-Depth)
- READ ONLY 트랜잭션으로 실행
- 타임아웃 및 결과 행 수 제한 적용
- 실행 시간 및 결과 메타데이터 수집

#### 7. Response Formatting (응답 포맷팅)
**파일**: `agent/nodes/response_formatting.py`

실행 결과를 사용자 친화적인 형태로 변환합니다.
- 결과 데이터를 Markdown 테이블로 포맷팅
- 에러 상황별 한국어 안내 메시지 생성
- 빈 결과, 타임아웃, 권한 오류 등 상황별 처리

### 상태 전이 로직

| 현재 노드 | 조건 | 다음 노드 |
|----------|------|----------|
| `permission_pre_check` | 권한 없음 | `response_formatting` (에러) |
| `permission_pre_check` | 권한 있음 | `schema_retrieval` |
| `schema_retrieval` | 스키마 조회 실패 | `response_formatting` (에러) |
| `schema_retrieval` | 스키마 조회 성공 | `query_generation` |
| `query_generation` | 최대 시도 초과 / 에러 | `response_formatting` (에러) |
| `query_generation` | 쿼리 생성 성공 | `query_validation` |
| `query_validation` | 검증 실패 & 재시도 가능 | `query_generation` |
| `query_validation` | 검증 실패 & 재시도 불가 | `response_formatting` (에러) |
| `query_validation` | 검증 성공 | `user_confirmation` |
| `user_confirmation` | 사용자 거부 | `response_formatting` (취소) |
| `user_confirmation` | 사용자 승인 | `query_execution` |
| `query_execution` | 실행 실패 | `response_formatting` (에러) |
| `query_execution` | 실행 성공 | `response_formatting` |

## 보안

### 쿼리 검증 3단계

생성된 SQL 쿼리는 실행 전 3단계 점진적 검증을 거칩니다. 각 단계에서 실패 시 즉시 반환하여 불필요한 검증 비용을 절감합니다.

#### 1단계: 키워드 검증 (`keyword_validator.py`)
**목적**: 위험한 DML/DDL 문 조기 차단
**시간 복잡도**: O(n) - 정규식 패턴 매칭

| 차단 키워드 | 위험 유형 |
|------------|----------|
| `UPDATE`, `DELETE`, `INSERT` | 데이터 변경 |
| `DROP`, `ALTER`, `TRUNCATE` | 스키마 변경 |
| `GRANT`, `REVOKE` | 권한 변경 |
| `CREATE`, `MODIFY` | 객체 생성/수정 |
| `EXEC`, `EXECUTE` | 프로시저 실행 |

- CTE (`WITH ... AS`) 구문을 SELECT 문으로 올바르게 처리
- 문자열 리터럴 내 키워드는 무시 (`'DELETE ME'` 허용)

#### 2단계: 스키마 검증 (`schema_validator.py`)
**목적**: 존재하지 않는 테이블/컬럼 참조 방지

- `information_schema`에서 실제 테이블/컬럼 목록 조회
- SQL 파싱으로 참조된 객체 추출
- 존재하지 않는 객체 접근 시 명확한 에러 메시지 제공

#### 3단계: 시맨틱 검증 (`semantic_validator.py`)
**목적**: LLM을 활용한 우회 시도 탐지

| 탐지 대상 | 예시 |
|----------|------|
| SQL Injection 시도 | `'; DROP TABLE users; --` |
| 권한 우회 시도 | 다른 사용자 데이터 접근 |
| 시스템 테이블 접근 | `pg_catalog`, `information_schema` 직접 쿼리 |
| 의도적 복잡화 | 중첩 서브쿼리로 키워드 검증 우회 |

- 빠른 패턴 검사 후 LLM 호출 (비용 최적화)
- 빠른 모델(GPT-3.5, Gemini Flash 등) 사용

### 실행 제한

- READ ONLY 트랜잭션 (`SET TRANSACTION READ ONLY`)
- 쿼리 타임아웃 설정 (`statement_timeout`)
- 결과 행 수 제한 (`LIMIT`)

### Defense-in-Depth 설계

워크플로우 전체에 걸쳐 다중 보안 레이어를 적용합니다:

```
1. Permission Pre-check  → 사용자 역할 기반 테이블 접근 제한
2. Schema Retrieval      → 접근 가능 테이블만 LLM에 제공
3. Query Validation      → 3단계 검증 파이프라인
4. User Confirmation     → Human-in-the-Loop 승인
5. Query Execution       → 최종 권한 재검증 + READ ONLY 실행
```

각 레이어는 이전 레이어가 실패할 수 있다고 가정하고 독립적으로 검증합니다.

## 환경 변수

| 변수 | 설명 | 기본값 |
|------|------|--------|
| `DATABASE_URL` | PostgreSQL 연결 문자열 | (필수) |
| `OPENAI_API_KEY` | OpenAI API 키 | - |
| `ANTHROPIC_API_KEY` | Anthropic API 키 | - |
| `GOOGLE_AI_API_KEY` | Google AI API 키 | - |
| `DEFAULT_LLM_PROVIDER` | 기본 LLM | openai |
| `LLM_TEMPERATURE` | LLM 온도 | 0.0 |
| `LLM_MAX_TOKENS` | 최대 토큰 수 | 2048 |
| `HOST` | 서버 호스트 | 0.0.0.0 |
| `PORT` | 서버 포트 | 8000 |
| `DEBUG` | 디버그 모드 | false |
| `LOG_LEVEL` | 로그 레벨 | INFO |
| `SESSION_TIMEOUT_MINUTES` | 세션 타임아웃 | 30 |
| `MAX_MESSAGE_HISTORY` | 최대 메시지 수 | 10 |
| `QUERY_TIMEOUT_MS` | 쿼리 타임아웃 | 30000 |
| `MAX_RESULT_ROWS` | 최대 결과 행 | 10000 |
| `AUTO_CONFIRM_QUERIES` | 자동 확인 모드 | true |
| `JWT_SECRET_KEY` | JWT 서명 비밀키 | (필수/변경요망) |
| `JWT_ALGORITHM` | JWT 알고리즘 | HS256 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 액세스 토큰 만료(분) | 30 |
| `REFRESH_TOKEN_EXPIRE_DAYS` | 리프레시 토큰 만료(일) | 7 |
| `CORS_ORIGINS` | CORS 허용 오리진 | ["http://localhost:3000"] |

## 테스트

```bash
# 전체 테스트
pytest

# 단위 테스트
pytest tests/unit/

# 통합 테스트
pytest tests/integration/

# 커버리지
pytest --cov=app --cov-report=html
```

## 코드 품질

```bash
# 린팅
ruff check .

# 포매팅
ruff format .

# 타입 체크
mypy src/
```

## 라이선스

MIT License
