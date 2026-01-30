# Tasks: Text2SQL Agent

**Input**: Design documents from `/specs/1-text2sql-agent/`
**Prerequisites**: plan.md (✓), spec.md (✓), research.md (✓), data-model.md (✓), contracts/api.yaml (✓)

**Tests**: Tests are included for critical paths (security validation, API contracts).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app structure**: `backend/src/app/`, `frontend/src/`
- Based on plan.md project structure

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create backend project structure per implementation plan (`backend/src/app/` with agent/, llm/, database/, validation/, session/, api/, models/, errors/ directories)
- [ ] T002 Initialize Python project with pyproject.toml (Python 3.11+, dependencies: langgraph, langchain, fastapi, asyncpg, pydantic)
- [ ] T003 [P] Create requirements.txt with pinned versions from plan.md dependencies
- [ ] T004 [P] Configure ruff for linting and formatting (pyproject.toml)
- [ ] T005 [P] Configure mypy with strict mode (pyproject.toml or mypy.ini)
- [ ] T006 [P] Create .env.example with required environment variables (DATABASE_URL, OPENAI_API_KEY, etc.)
- [ ] T007 [P] Create frontend project structure per implementation plan (`frontend/src/` with components/, hooks/, services/, types/)
- [ ] T008 [P] Initialize frontend project with package.json (React 18, @tanstack/react-query, tailwindcss, vite)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T009 Implement configuration management with Pydantic Settings in `backend/src/app/config.py`
- [ ] T010 [P] Create base Pydantic models for API schemas in `backend/src/app/models/entities.py` (Message, ConversationSession, QueryRequest, GeneratedQuery, QueryResult, DatabaseSchema)
- [ ] T011 [P] Create API request/response models in `backend/src/app/models/requests.py` and `backend/src/app/models/responses.py`
- [ ] T012 [P] Define custom exception classes in `backend/src/app/errors/exceptions.py` (Text2SQLError, DangerousQueryError, QueryTimeoutError, ValidationError, SchemaNotFoundError)
- [ ] T013 [P] Implement error handlers for FastAPI in `backend/src/app/errors/handlers.py`
- [ ] T014 Implement asyncpg connection pool in `backend/src/app/database/connection.py`
- [ ] T015 Create database schema extraction from information_schema in `backend/src/app/database/schema.py`
- [ ] T016 [P] Define LangGraph agent state (TypedDict) in `backend/src/app/agent/state.py`
- [ ] T017 Create LLM protocol and factory pattern in `backend/src/app/llm/base.py` and `backend/src/app/llm/factory.py`
- [ ] T018 [P] Implement OpenAI LLM provider in `backend/src/app/llm/openai.py`
- [ ] T019 [P] Implement Anthropic LLM provider in `backend/src/app/llm/anthropic.py`
- [ ] T020 [P] Implement Google LLM provider in `backend/src/app/llm/google.py`
- [ ] T021 Create FastAPI app entry point with CORS and middleware in `backend/src/app/main.py`
- [ ] T022 [P] Create health check endpoint in `backend/src/app/api/routes/health.py`
- [ ] T023 Setup pytest configuration in `backend/tests/conftest.py` with async fixtures

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - 자연어 질문으로 데이터 조회하기 (Priority: P1) 🎯 MVP

**Goal**: 비개발자가 자연어로 질문하면 SQL 쿼리를 생성하고 결과를 표시

**Independent Test**: "지난달 매출 상위 10개 제품이 뭐야?" 입력 시 쿼리 생성 및 결과 반환 확인

### Tests for User Story 1

- [ ] T024 [P] [US1] Contract test for POST /api/chat endpoint in `backend/tests/contract/test_chat_api.py`
- [ ] T025 [P] [US1] Integration test for query generation flow in `backend/tests/integration/test_query_generation.py`

### Implementation for User Story 1

- [ ] T026 [US1] Implement schema retrieval node in `backend/src/app/agent/nodes/schema_retrieval.py`
- [ ] T027 [US1] Implement query generation node with LLM in `backend/src/app/agent/nodes/query_generation.py`
- [ ] T028 [US1] Implement query execution node in `backend/src/app/agent/nodes/query_execution.py`
- [ ] T029 [US1] Implement safe query executor in `backend/src/app/database/executor.py` (READ ONLY transaction, timeout, row limit)
- [ ] T030 [US1] Implement response formatting node in `backend/src/app/agent/nodes/response_formatting.py`
- [ ] T031 [US1] Build LangGraph workflow in `backend/src/app/agent/graph.py` (schema → generation → execution → formatting)
- [ ] T032 [US1] Implement session manager with MemorySaver checkpointer in `backend/src/app/session/manager.py`
- [ ] T033 [US1] Implement chat endpoint with SSE streaming in `backend/src/app/api/routes/chat.py`
- [ ] T034 [US1] Create FastAPI dependencies for DB pool and LLM in `backend/src/app/api/dependencies.py`

**Checkpoint**: User Story 1 should be fully functional - natural language queries can be converted to SQL and executed

---

## Phase 4: User Story 2 - 위험한 쿼리 차단 (Priority: P1) 🎯 MVP

**Goal**: UPDATE, DELETE, DROP 등 데이터 변경 쿼리를 100% 차단

**Independent Test**: "고객 정보를 삭제해줘" 입력 시 차단 메시지 확인

### Tests for User Story 2

- [ ] T035 [P] [US2] Unit test for keyword validator with all dangerous keywords in `backend/tests/unit/test_keyword_validator.py`
- [ ] T036 [P] [US2] Unit test for schema validator in `backend/tests/unit/test_schema_validator.py`
- [ ] T037 [P] [US2] Integration test for dangerous query blocking in `backend/tests/integration/test_dangerous_query_blocking.py`

### Implementation for User Story 2

- [ ] T038 [US2] Implement Layer 1 keyword-based safety validator in `backend/src/app/validation/keyword_validator.py` (UPDATE, DELETE, INSERT, DROP, ALTER, TRUNCATE, GRANT, REVOKE, CREATE, MODIFY, EXEC, EXECUTE)
- [ ] T039 [US2] Implement Layer 2 schema validation in `backend/src/app/validation/schema_validator.py` (table/column existence check)
- [ ] T040 [US2] Implement Layer 3 LLM semantic validator in `backend/src/app/validation/semantic_validator.py`
- [ ] T041 [US2] Implement query validation node in `backend/src/app/agent/nodes/query_validation.py` (3-layer progressive validation)
- [ ] T042 [US2] Update LangGraph workflow to include validation node with retry logic (max 3 attempts) in `backend/src/app/agent/graph.py`

**Checkpoint**: User Story 2 should be fully functional - all dangerous queries are blocked with user-friendly messages

---

## Phase 5: User Story 3 - 쿼리 검증 및 결과 미리보기 (Priority: P2)

**Goal**: 쿼리 실행 전 사용자 확인을 받는 Human-in-the-Loop 구현

**Independent Test**: 질문 후 쿼리와 설명이 표시되고, 확인/취소 버튼으로 제어 가능한지 확인

### Tests for User Story 3

- [ ] T043 [P] [US3] Contract test for POST /api/chat/confirm endpoint in `backend/tests/contract/test_confirm_api.py`
- [ ] T044 [P] [US3] Integration test for Human-in-the-Loop flow in `backend/tests/integration/test_human_in_loop.py`

### Implementation for User Story 3

- [ ] T045 [US3] Implement user confirmation node with LangGraph interrupt() in `backend/src/app/agent/nodes/user_confirmation.py`
- [ ] T046 [US3] Update LangGraph workflow to include confirmation interrupt after validation in `backend/src/app/agent/graph.py`
- [ ] T047 [US3] Implement confirmation endpoint with Command(resume) in `backend/src/app/api/routes/chat.py`
- [ ] T048 [US3] Add query explanation generation (Korean) in query generation node
- [ ] T049 [P] [US3] Implement QueryPreview component in `frontend/src/components/Chat/QueryPreview.tsx`
- [ ] T050 [P] [US3] Implement confirmation buttons (실행/취소) in QueryPreview component

**Checkpoint**: User Story 3 should be fully functional - users can preview and approve queries before execution

---

## Phase 6: User Story 4 - 오류 상황 안내 (Priority: P2)

**Goal**: 모든 오류 상황에서 비개발자가 이해할 수 있는 한국어 안내 메시지 제공

**Independent Test**: 모호한 질문, DB 연결 오류, 빈 결과 등에서 친절한 메시지 표시 확인

### Tests for User Story 4

- [ ] T051 [P] [US4] Unit test for error message generation in `backend/tests/unit/test_error_messages.py`
- [ ] T052 [P] [US4] Integration test for error scenarios in `backend/tests/integration/test_error_handling.py`

### Implementation for User Story 4

- [ ] T053 [US4] Define Korean error message templates for all error codes in `backend/src/app/errors/messages.py`
- [ ] T054 [US4] Implement ambiguous query detection and helpful suggestions in query generation node
- [ ] T055 [US4] Handle database connection errors with user-friendly messages
- [ ] T056 [US4] Handle empty result set with appropriate message ("조건에 맞는 데이터가 없습니다")
- [ ] T057 [US4] Handle query timeout with suggestion to add more specific conditions
- [ ] T058 [P] [US4] Implement ErrorMessage component in `frontend/src/components/common/ErrorMessage.tsx`

**Checkpoint**: User Story 4 should be fully functional - all errors show user-friendly Korean messages

---

## Phase 7: User Story 5 - 대화 맥락 유지 (Priority: P3)

**Goal**: 연속 질문에서 이전 대화 맥락을 유지

**Independent Test**: "지난달 매출 보여줘" → "그중에 서울 지역만" 연속 질문이 정상 동작하는지 확인

### Tests for User Story 5

- [ ] T059 [P] [US5] Integration test for context-aware queries in `backend/tests/integration/test_conversation_context.py`

### Implementation for User Story 5

- [ ] T060 [US5] Implement message history management with add_messages reducer in agent state
- [ ] T061 [US5] Enhance query generation prompt to include conversation context
- [ ] T062 [US5] Implement context reference detection (e.g., "그중에", "거기서") in `backend/src/app/agent/nodes/query_generation.py`
- [ ] T063 [US5] Implement session reset on "처음부터 다시" command
- [ ] T064 [US5] Add session timeout handling (30분) in session manager

**Checkpoint**: User Story 5 should be fully functional - users can have contextual conversations

---

## Phase 8: Frontend Implementation

**Purpose**: Web chat UI for user interaction

- [ ] T065 [P] Create TypeScript types matching API schemas in `frontend/src/types/index.ts`
- [ ] T066 [P] Implement API service with SSE support in `frontend/src/services/api.ts`
- [ ] T067 [P] Create useSession hook in `frontend/src/hooks/useSession.ts`
- [ ] T068 [P] Create useChat hook with SSE handling in `frontend/src/hooks/useChat.ts`
- [ ] T069 Implement ChatContainer component in `frontend/src/components/Chat/ChatContainer.tsx`
- [ ] T070 [P] Implement MessageList component in `frontend/src/components/Chat/MessageList.tsx`
- [ ] T071 [P] Implement MessageInput component in `frontend/src/components/Chat/MessageInput.tsx`
- [ ] T072 [P] Implement ResultTable component with pagination in `frontend/src/components/Chat/ResultTable.tsx`
- [ ] T073 [P] Implement LoadingSpinner component in `frontend/src/components/common/LoadingSpinner.tsx`
- [ ] T074 Create App.tsx with React Query provider and main layout in `frontend/src/App.tsx`
- [ ] T075 [P] Configure Tailwind CSS in `frontend/tailwind.config.js`
- [ ] T076 [P] Configure Vite in `frontend/vite.config.ts`

---

## Phase 9: API Endpoints Completion

**Purpose**: Additional API endpoints per OpenAPI contract

- [ ] T077 [P] Implement session creation endpoint in `backend/src/app/api/routes/session.py`
- [ ] T078 [P] Implement session retrieval endpoint in `backend/src/app/api/routes/session.py`
- [ ] T079 [P] Implement session termination endpoint in `backend/src/app/api/routes/session.py`
- [ ] T080 [P] Implement schema retrieval endpoint in `backend/src/app/api/routes/schema.py`
- [ ] T081 [P] Implement schema refresh endpoint in `backend/src/app/api/routes/schema.py`
- [ ] T082 Register all routers in main.py

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T083 [P] Add logging configuration with structured logging in `backend/src/app/config.py`
- [ ] T084 [P] Add request logging middleware in `backend/src/app/main.py`
- [ ] T085 Code cleanup and type annotation verification with mypy
- [ ] T086 [P] Run ruff linting and formatting on all Python files
- [ ] T087 [P] Create Dockerfile for backend in `backend/Dockerfile`
- [ ] T088 [P] Create Dockerfile for frontend in `frontend/Dockerfile`
- [ ] T089 [P] Create docker-compose.yml for local development
- [ ] T090 Run quickstart.md validation (verify all steps work)
- [ ] T091 Security review: verify all SQL queries use parameterized execution
- [ ] T092 Performance test: verify 10-second response time target

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-7)**: All depend on Foundational phase completion
  - US1 and US2 (both P1) should be implemented together for MVP
  - US3 and US4 (both P2) can proceed after P1 stories
  - US5 (P3) can proceed after P2 stories
- **Frontend (Phase 8)**: Can start after Foundational (Phase 2), parallel with backend stories
- **API Endpoints (Phase 9)**: Depends on Foundational (Phase 2)
- **Polish (Phase 10)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - Core query generation
- **User Story 2 (P1)**: Can start after US1 begins - Adds validation layer to US1 flow
- **User Story 3 (P2)**: Depends on US1 and US2 - Adds Human-in-the-Loop
- **User Story 4 (P2)**: Can run parallel with US3 - Independent error handling
- **User Story 5 (P3)**: Depends on US1 - Extends conversation capability

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Nodes before graph composition
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- All tests for a user story marked [P] can run in parallel
- Frontend Phase 8 can run in parallel with backend Phases 3-7
- Different user stories can be worked on in parallel by different team members

---

## Implementation Strategy

### MVP First (User Stories 1 + 2)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Query Generation)
4. Complete Phase 4: User Story 2 (Security Validation)
5. **STOP and VALIDATE**: Test end-to-end query flow with dangerous query blocking
6. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Stories 1+2 → MVP with security
3. Add User Story 3 → Human-in-the-Loop confirmation
4. Add User Story 4 → Complete error handling
5. Add User Story 5 → Conversation context
6. Complete Frontend → Full web UI

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- 위험 쿼리 차단 (US2)은 보안 요구사항이므로 US1과 함께 MVP에 반드시 포함
