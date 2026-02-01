# Text2SQL Agent

자연어를 SQL 쿼리로 변환하고 실행하는 AI 에이전트 시스템입니다.

## 개요

Text2SQL Agent는 비개발자도 자연어로 데이터베이스를 조회할 수 있게 해주는 웹 애플리케이션입니다. LangGraph 기반의 AI 에이전트가 사용자의 질문을 이해하고, 안전한 SQL 쿼리를 생성하여 실행합니다.

### 주요 기능

- **자연어 쿼리**: "지난달 매출 상위 10개 제품이 뭐야?" 같은 자연어 질문을 SQL로 변환
- **위험 쿼리 차단**: UPDATE, DELETE, DROP 등 데이터 변경 쿼리를 3단계 검증으로 100% 차단
- **Human-in-the-Loop**: 쿼리 실행 전 사용자 확인을 통한 안전한 실행
- **대화 맥락 유지**: "그중에 서울 지역만" 같은 연속 질문 지원
- **사용자 친화적 오류 처리**: 모든 오류 상황에서 한국어 안내 메시지 제공

## 기술 스택

### Backend
- **Python 3.11+**
- **FastAPI** - 비동기 웹 프레임워크
- **LangGraph 1.0+** - AI 에이전트 워크플로우
- **LangChain 1.2+** - LLM 통합
- **PostgreSQL** - 대상 데이터베이스
- **asyncpg** - 비동기 PostgreSQL 드라이버

### Frontend
- **React 18** - UI 라이브러리
- **TypeScript** - 타입 안전성
- **TanStack Query** - 서버 상태 관리
- **Tailwind CSS** - 스타일링
- **Vite** - 빌드 도구

### Infrastructure
- **Docker** - 컨테이너화
- **Nginx** - 프론트엔드 서빙 및 리버스 프록시

## 프로젝트 구조

```
text2sql/
├── backend/                 # 백엔드 API 서버
│   ├── src/app/
│   │   ├── agent/          # LangGraph 에이전트
│   │   ├── api/            # FastAPI 라우터
│   │   ├── database/       # DB 연결 및 스키마
│   │   ├── llm/            # LLM 프로바이더
│   │   ├── validation/     # 쿼리 검증
│   │   └── session/        # 세션 관리
│   ├── tests/              # 테스트
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/               # 프론트엔드 웹 앱
│   ├── src/
│   │   ├── components/     # React 컴포넌트
│   │   ├── hooks/          # 커스텀 훅
│   │   ├── services/       # API 서비스
│   │   └── types/          # TypeScript 타입
│   ├── Dockerfile
│   └── package.json
├── specs/                  # 설계 문서
│   └── 1-text2sql-agent/
│       ├── spec.md         # 기능 명세
│       ├── plan.md         # 구현 계획
│       └── tasks.md        # 작업 목록
└── docker-compose.yml      # 전체 스택 실행
```

## 빠른 시작

### 사전 요구사항

- Docker 및 Docker Compose
- OpenAI API 키 (또는 Anthropic/Google AI API 키)

### 1. 환경 변수 설정

```bash
# .env 파일 생성
cat > .env << EOF
OPENAI_API_KEY=your-openai-api-key
POSTGRES_USER=text2sql
POSTGRES_PASSWORD=text2sql_dev
POSTGRES_DB=text2sql_db
DEBUG=true
EOF
```

### 2. Docker Compose로 실행

```bash
# 전체 스택 빌드 및 실행
docker-compose up --build

# 백그라운드 실행
docker-compose up -d --build
```

### 3. 접속

- **프론트엔드**: http://localhost:3000
- **백엔드 API**: http://localhost:8000
- **API 문서**: http://localhost:8000/docs (DEBUG=true일 때)

## 로컬 개발

### 백엔드

```bash
cd backend

# 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정
export DATABASE_URL=postgresql://user:pass@localhost:5432/dbname
export OPENAI_API_KEY=your-key

# 서버 실행
python -m app.main
```

### 프론트엔드

```bash
cd frontend

# 의존성 설치
npm install

# 개발 서버 실행
npm run dev
```

## API 엔드포인트

| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/api/chat` | 자연어 질문 처리 (SSE 스트리밍) |
| POST | `/api/chat/confirm` | 쿼리 실행 확인/취소 |
| POST | `/api/sessions` | 새 세션 생성 |
| GET | `/api/sessions/{id}` | 세션 조회 |
| DELETE | `/api/sessions/{id}` | 세션 종료 |
| GET | `/api/schema` | DB 스키마 조회 |
| POST | `/api/schema/refresh` | 스키마 캐시 갱신 |
| GET | `/api/health` | 헬스체크 |

## 보안

### 쿼리 검증 3단계

1. **키워드 검증**: UPDATE, DELETE, INSERT, DROP 등 위험 키워드 차단
2. **스키마 검증**: 존재하지 않는 테이블/컬럼 참조 차단
3. **시맨틱 검증**: LLM을 통한 의도 분석으로 우회 시도 차단

### 실행 제한

- READ ONLY 트랜잭션으로 실행
- 쿼리 타임아웃 (기본 30초)
- 결과 행 수 제한 (기본 10,000행)

## 지원 LLM

- **OpenAI**: GPT-4o, GPT-4o-mini (기본)
- **Anthropic**: Claude 3.5 Sonnet
- **Google**: Gemini 1.5 Pro

## 환경 변수

| 변수 | 설명 | 기본값 |
|------|------|--------|
| `DATABASE_URL` | PostgreSQL 연결 문자열 | (필수) |
| `OPENAI_API_KEY` | OpenAI API 키 | - |
| `ANTHROPIC_API_KEY` | Anthropic API 키 | - |
| `GOOGLE_AI_API_KEY` | Google AI API 키 | - |
| `DEFAULT_LLM_PROVIDER` | 기본 LLM 제공자 | openai |
| `DEBUG` | 디버그 모드 | false |
| `LOG_LEVEL` | 로그 레벨 | INFO |
| `SESSION_TIMEOUT_MINUTES` | 세션 타임아웃 | 30 |
| `QUERY_TIMEOUT_MS` | 쿼리 타임아웃 | 30000 |
| `MAX_RESULT_ROWS` | 최대 결과 행 수 | 10000 |

## 라이선스

MIT License
