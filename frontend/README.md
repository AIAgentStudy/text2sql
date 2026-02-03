# Text2SQL Agent - Frontend

자연어 데이터베이스 조회를 위한 웹 채팅 인터페이스입니다.

## 개요

React와 TypeScript로 구축된 SPA(Single Page Application)로, SSE(Server-Sent Events)를 통해 백엔드 API와 실시간으로 통신합니다.

## 기술 스택

- **React 18** - UI 라이브러리
- **TypeScript** - 타입 안전성
- **TanStack Query (React Query)** - 서버 상태 관리
- **React Router** - 클라이언트 사이드 라우팅
- **Tailwind CSS** - 유틸리티 기반 스타일링
- **Vite** - 빌드 도구
- **serve** - 프로덕션 정적 파일 서빙

## 프로젝트 구조

```
frontend/
├── src/
│   ├── components/         # React 컴포넌트
│   │   ├── Auth/           # 인증 관련 컴포넌트
│   │   ├── Chat/
│   │   │   ├── ChatContainer.tsx   # 채팅 메인 컨테이너
│   │   │   ├── MessageList.tsx     # 메시지 목록
│   │   │   ├── MessageInput.tsx    # 입력창
│   │   │   ├── QueryPreview.tsx    # 쿼리 미리보기
│   │   │   └── ResultTable.tsx     # 결과 테이블
│   │   └── common/
│   │       ├── ErrorMessage.tsx    # 에러 메시지
│   │       └── LoadingSpinner.tsx  # 로딩 스피너
│   ├── hooks/              # 커스텀 훅
│   │   ├── useSession.ts   # 세션 관리
│   │   └── useChat.ts      # 채팅 및 SSE 처리
│   ├── pages/              # 페이지 컴포넌트
│   │   ├── LoginPage.tsx
│   │   ├── RegisterPage.tsx
│   │   ├── ChatPage.tsx
│   │   └── GuidePage.tsx
│   ├── services/           # API 서비스
│   │   └── api.ts          # API 클라이언트
│   ├── types/              # TypeScript 타입
│   │   └── index.ts        # 타입 정의
│   ├── App.tsx             # 메인 앱 컴포넌트
│   ├── main.tsx            # 엔트리포인트
│   └── index.css           # 글로벌 스타일
├── public/                 # 정적 파일
├── index.html              # HTML 템플릿
├── tailwind.config.js      # Tailwind 설정
├── vite.config.ts          # Vite 설정
├── tsconfig.json           # TypeScript 설정
├── package.json
└── Dockerfile
```

## 설치 및 실행

### 요구사항

- Node.js 18+
- npm 또는 yarn

### 로컬 개발

```bash
# 의존성 설치
npm install

# 개발 서버 실행 (http://localhost:3000)
npm run dev

# 타입 체크
npm run type-check

# 린팅
npm run lint

# 프로덕션 빌드
npm run build

# 빌드 미리보기
npm run preview
```

### Docker

```bash
# 이미지 빌드
docker build -t text2sql-frontend .

# 컨테이너 실행
docker run -p 3000:80 text2sql-frontend
```

## 주요 컴포넌트

### Pages

- **LoginPage**: 사용자 로그인 페이지
- **RegisterPage**: 회원가입 페이지
- **ChatPage**: 메인 채팅 인터페이스
- **GuidePage**: 사용 가이드 및 도움말 페이지

### ChatContainer

채팅 UI의 메인 컨테이너입니다. `useSession`과 `useChat` 훅을 사용하여 상태를 관리합니다.

```tsx
import { ChatContainer } from './components/Chat/ChatContainer';

<ChatContainer llmProvider="openai" />
```

### MessageList

채팅 메시지 목록을 표시합니다. 자동 스크롤과 메시지 타입별 렌더링을 지원합니다.

- 사용자 메시지
- 어시스턴트 메시지
- 쿼리 미리보기
- 쿼리 결과 테이블
- 에러 메시지

### MessageInput

메시지 입력창입니다. Enter로 전송, Shift+Enter로 줄바꿈을 지원합니다.

### QueryPreview

생성된 SQL 쿼리를 미리보기하고, 실행 또는 취소할 수 있는 컴포넌트입니다.

- 쿼리 설명 (한국어)
- SQL 코드 하이라이팅
- 쿼리 수정 기능 (선택적)
- 실행/취소 버튼

### ResultTable

쿼리 결과를 테이블 형태로 표시합니다.

- 페이지네이션
- 컬럼 정렬
- 데이터 타입별 포맷팅
- 결과 요약 정보

## 커스텀 훅

### useSession

세션 관리를 위한 훅입니다.

```tsx
const {
  session,           // 현재 세션 정보
  sessionId,         // 세션 ID
  isLoading,         // 로딩 상태
  error,             // 에러
  createNewSession,  // 새 세션 생성
  restoreSession,    // 기존 세션 복구
  terminateSession,  // 세션 종료
  clearSession,      // 로컬 상태 초기화
  setSessionId,      // 세션 ID 설정
} = useSession({
  autoRestore: true,           // 자동 복구 시도
  defaultLLMProvider: 'openai' // 기본 LLM
});
```

### useChat

채팅 및 SSE 스트리밍을 처리하는 훅입니다.

```tsx
const {
  messages,              // 메시지 목록
  isLoading,             // 로딩 상태
  currentStatus,         // 현재 상태
  awaitingConfirmation,  // 확인 대기 중
  pendingQueryId,        // 대기 중인 쿼리 ID
  error,                 // 에러
  sendMessage,           // 메시지 전송
  confirmQuery,          // 쿼리 확인/취소
  cancelRequest,         // 요청 취소
  clearChat,             // 채팅 초기화
  clearError,            // 에러 초기화
} = useChat({
  sessionId,
  llmProvider: 'openai',
  onSessionId: (id) => setSessionId(id),
  onConfirmationRequired: (queryId, query, explanation) => { ... }
});
```

## API 서비스

### SSE 스트리밍

```tsx
import { streamChat, SSEEventHandlers } from './services/api';

const handlers: SSEEventHandlers = {
  onSession: (event) => { /* 세션 이벤트 */ },
  onStatus: (event) => { /* 상태 이벤트 */ },
  onQueryPreview: (event) => { /* 쿼리 미리보기 */ },
  onConfirmationRequired: (event) => { /* 확인 필요 */ },
  onResult: (event) => { /* 결과 */ },
  onError: (event) => { /* 에러 */ },
  onDone: (event) => { /* 완료 */ },
};

await streamChat(
  { session_id: null, message: '질문', llm_provider: 'openai' },
  handlers,
  abortController.signal
);
```

### REST API

```tsx
import { api } from './services/api';

// 세션
const session = await api.createSession({ llm_provider: 'openai' });
const session = await api.getSession(sessionId);
await api.terminateSession(sessionId);

// 쿼리 확인
const result = await api.confirmQuery({
  session_id: sessionId,
  query_id: queryId,
  approved: true
});

// 스키마
const schema = await api.getSchema();
const schema = await api.refreshSchema();

// 헬스체크
const health = await api.checkHealth();
```

## 타입 정의

주요 타입들은 `src/types/index.ts`에 정의되어 있습니다.

```tsx
// 메시지 역할
type MessageRole = 'user' | 'assistant' | 'system';

// 쿼리 상태
type QueryRequestStatus =
  | 'pending'
  | 'generating'
  | 'validating'
  | 'awaiting_confirm'
  | 'executing'
  | 'completed'
  | 'failed'
  | 'cancelled';

// 채팅 메시지
interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: Date;
  queryPreview?: { query: string; explanation: string; queryId: string };
  queryResult?: QueryResultData;
  error?: ErrorDetail;
  isLoading?: boolean;
}

// 쿼리 결과
interface QueryResultData {
  rows: Record<string, unknown>[];
  total_row_count: number;
  returned_row_count: number;
  columns: ColumnInfo[];
  is_truncated: boolean;
  execution_time_ms: number;
}
```

## 환경 변수

| 변수 | 설명 | 기본값 |
|------|------|--------|
| `VITE_API_BASE_URL` | 백엔드 API URL | http://localhost:8000 |

`.env` 파일 예시:
```
VITE_API_BASE_URL=http://localhost:8000
```

## Vite 설정

개발 환경에서 백엔드 API로 프록시가 설정되어 있습니다.

```ts
// vite.config.ts
export default defineConfig({
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
});
```

## 프로덕션 서빙

프로덕션 환경에서 `serve` 패키지를 사용하여 정적 파일을 서빙합니다.

- SPA 라우팅 지원 (`-s` 플래그)
- 포트 3000에서 서빙
- API 요청은 `VITE_API_BASE_URL` 환경 변수로 설정된 백엔드로 직접 전송

## 스타일링

Tailwind CSS를 사용합니다. 설정은 `tailwind.config.js`에 있습니다.

### 주요 스타일 클래스

```css
/* 메시지 버블 */
.bg-blue-600  /* 사용자 메시지 */
.bg-gray-100  /* 어시스턴트 메시지 */

/* 쿼리 코드 블록 */
.bg-gray-900 .text-green-400  /* SQL 코드 */

/* 버튼 */
.bg-blue-600 hover:bg-blue-700  /* 기본 버튼 */
.border-gray-300 hover:bg-gray-50  /* 보조 버튼 */
```

## 라이선스

MIT License
