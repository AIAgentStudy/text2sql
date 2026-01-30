# Implementation Plan: Text2SQL Agent

**Branch**: `1-text2sql-agent` | **Date**: 2025-01-30 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/1-text2sql-agent/spec.md`

## Summary

비개발자가 자연어로 데이터베이스를 조회할 수 있는 Text-to-SQL Agent 구현. LangGraph (Python) 기반 워크플로우로 쿼리 생성, 다중 레이어 검증, 사용자 확인(Human-in-the-Loop), 안전한 실행을 순차적으로 처리. SELECT 전용으로 위험 쿼리를 100% 차단하고, 웹 채팅 UI를 통해 사용자 친화적 경험 제공.

## Technical Context

**Language/Version**: Python 3.11+ (with type hints, strict mypy)
**Primary Dependencies**:
- LangGraph (langgraph) - Agent 워크플로우 오케스트레이션
- LangChain (langchain, langchain-openai, langchain-anthropic, langchain-google-genai) - LLM 통합
- FastAPI - 비동기 API 서버
- React - 웹 채팅 UI (프론트엔드)
- asyncpg - PostgreSQL 비동기 클라이언트
- Pydantic v2 - 데이터 검증 및 직렬화

**Storage**: PostgreSQL (pgvector 확장 포함)
**Testing**: pytest + pytest-asyncio (단위/통합 테스트)
**Target Platform**: Linux/Docker (서버), Modern browsers (클라이언트)
**Project Type**: Web application (backend + frontend)
**Performance Goals**: 질문 입력부터 결과 표시까지 10초 이내
**Constraints**: 동시 접속 50명 지원, 쿼리 실행 타임아웃 30초
**Scale/Scope**: 비개발자 대상, 단일 PostgreSQL 인스턴스 연결

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Type Safety | ✅ Pass | Python type hints + mypy strict, Pydantic 모델 전체 사용 |
| II. Modular Architecture | ✅ Pass | Agent 노드별 독립 모듈, LLM 프로바이더 추상화, 검증 레이어 분리 |
| III. Test-First Development | ✅ Pass | 위험 쿼리 차단 테스트, 통합 테스트 우선 작성 예정 |
| IV. Simplicity First | ✅ Pass | LangGraph 단일 그래프, 불필요한 추상화 배제 |
| V. Documentation as Code | ✅ Pass | Google style docstrings, 모듈별 README, OpenAPI 자동 생성 |

## Project Structure

### Documentation (this feature)

```text
specs/1-text2sql-agent/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (OpenAPI specs)
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── src/
│   └── app/
│       ├── __init__.py
│       ├── main.py                   # FastAPI 앱 엔트리포인트
│       ├── config.py                 # 설정 관리 (Pydantic Settings)
│       ├── agent/                    # LangGraph Agent 모듈
│       │   ├── __init__.py
│       │   ├── graph.py              # Agent 그래프 빌더 및 컴파일
│       │   ├── state.py              # Agent 상태 정의 (TypedDict)
│       │   └── nodes/                # 그래프 노드들
│       │       ├── __init__.py
│       │       ├── schema_retrieval.py
│       │       ├── query_generation.py
│       │       ├── query_validation.py
│       │       ├── user_confirmation.py
│       │       ├── query_execution.py
│       │       └── response_formatting.py
│       ├── llm/                      # LLM 프로바이더 추상화
│       │   ├── __init__.py
│       │   ├── base.py               # 추상 인터페이스 (Protocol)
│       │   ├── factory.py            # 팩토리 패턴
│       │   ├── openai.py
│       │   ├── anthropic.py
│       │   └── google.py
│       ├── database/                 # 데이터베이스 연결 및 스키마
│       │   ├── __init__.py
│       │   ├── connection.py         # asyncpg 연결 풀
│       │   ├── schema.py             # 스키마 추출 (information_schema)
│       │   └── executor.py           # 안전한 쿼리 실행
│       ├── validation/               # SQL 검증 모듈
│       │   ├── __init__.py
│       │   ├── keyword_validator.py  # Layer 1: 위험 키워드 차단
│       │   ├── schema_validator.py   # Layer 2: 스키마 검증
│       │   └── semantic_validator.py # Layer 3: LLM 기반 검증
│       ├── session/                  # 세션 관리
│       │   ├── __init__.py
│       │   └── manager.py
│       ├── api/                      # API 라우터
│       │   ├── __init__.py
│       │   ├── routes/
│       │   │   ├── __init__.py
│       │   │   ├── chat.py           # 채팅 엔드포인트
│       │   │   ├── session.py        # 세션 관리 엔드포인트
│       │   │   ├── schema.py         # 스키마 조회 엔드포인트
│       │   │   └── health.py         # 헬스체크
│       │   └── dependencies.py       # FastAPI 의존성
│       ├── models/                   # Pydantic 모델 (API 스키마)
│       │   ├── __init__.py
│       │   ├── requests.py
│       │   ├── responses.py
│       │   └── entities.py
│       └── errors/                   # 에러 타입 및 핸들러
│           ├── __init__.py
│           ├── exceptions.py
│           └── handlers.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py                   # pytest fixtures
│   ├── unit/
│   │   ├── __init__.py
│   │   ├── test_validation.py
│   │   └── test_llm.py
│   ├── integration/
│   │   ├── __init__.py
│   │   ├── test_agent.py
│   │   └── test_api.py
│   └── contract/
│       ├── __init__.py
│       └── test_api_contract.py
├── pyproject.toml                    # 프로젝트 설정 (Poetry/PDM)
├── requirements.txt                  # 의존성 (pip)
└── Dockerfile

frontend/
├── src/
│   ├── components/
│   │   ├── Chat/
│   │   │   ├── ChatContainer.tsx
│   │   │   ├── MessageList.tsx
│   │   │   ├── MessageInput.tsx
│   │   │   ├── QueryPreview.tsx      # 쿼리 확인 UI
│   │   │   └── ResultTable.tsx       # 결과 테이블
│   │   └── common/
│   │       ├── LoadingSpinner.tsx
│   │       └── ErrorMessage.tsx
│   ├── hooks/
│   │   ├── useChat.ts
│   │   └── useSession.ts
│   ├── services/
│   │   └── api.ts
│   ├── types/
│   │   └── index.ts
│   └── App.tsx
├── package.json
└── vite.config.ts
```

**Structure Decision**: Web application 구조 선택. LangGraph Agent는 Python 백엔드에서 실행되며 FastAPI로 API 제공. 웹 채팅 UI는 React로 구현. 백엔드와 프론트엔드는 OpenAPI 스키마로 계약 공유.

## Complexity Tracking

> No violations detected. Design follows constitution principles.

| Aspect | Decision | Rationale |
|--------|----------|-----------|
| LLM 다중 지원 | 프로바이더 추상화 레이어 (Protocol) | 현재 요구사항 (GPT-4 + Claude + Gemini) 충족 |
| 검증 레이어 | 3단계 검증 | 각 레이어가 명확한 책임 보유, 빠른 것부터 순차 실행 |
| Human-in-the-Loop | LangGraph interrupt 사용 | 프레임워크 내장 기능 활용, 커스텀 구현 불필요 |
| API 스트리밍 | FastAPI StreamingResponse + SSE | 실시간 진행 상황 표시 |
