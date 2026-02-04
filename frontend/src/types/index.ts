/**
 * API 스키마와 일치하는 TypeScript 타입 정의
 *
 * backend/src/app/models/ 의 Pydantic 모델과 동기화됩니다.
 */

// === 열거형 ===

export type QueryRequestStatus =
  | 'pending'
  | 'generating'
  | 'validating'
  | 'awaiting_confirm'
  | 'executing'
  | 'completed'
  | 'failed'
  | 'cancelled';

export type ValidationStatus = 'pending' | 'valid' | 'invalid';

export type SessionStatus = 'active' | 'expired' | 'terminated';

export type LLMProvider = 'openai' | 'anthropic' | 'google';

export type MessageRole = 'user' | 'assistant' | 'system';

// === 기본 엔티티 ===

export interface Message {
  role: MessageRole;
  content: string;
  timestamp: string;
}

export interface ColumnInfo {
  name: string;
  data_type: string;
  is_nullable: boolean;
}

export interface ValidationError {
  layer: 'keyword' | 'schema' | 'semantic';
  code: string;
  message: string;
  severity: 'error' | 'warning';
}

// === 요청 타입 ===

export interface ChatRequest {
  session_id?: string | null;
  message: string;
  llm_provider?: LLMProvider;
}

export interface ConfirmationRequest {
  session_id: string;
  query_id: string;
  approved: boolean;
}

export interface CreateSessionRequest {
  llm_provider?: LLMProvider;
}

// === 응답 타입 ===

export interface ErrorDetail {
  code: string;
  message: string;
}

export interface QueryResultData {
  rows: Record<string, unknown>[];
  total_row_count: number;
  returned_row_count: number;
  columns: ColumnInfo[];
  is_truncated: boolean;
  execution_time_ms: number;
}

export interface SessionResponse {
  session_id: string;
  status: SessionStatus;
  llm_provider: LLMProvider;
  created_at: string;
  last_activity_at: string;
  message_history: Message[];
}

export interface ConfirmationResponse {
  success: boolean;
  result?: QueryResultData | null;
  error?: ErrorDetail | null;
}

export interface HealthDependencies {
  database: 'ok' | 'error';
}

export interface HealthResponse {
  status: 'healthy' | 'unhealthy';
  timestamp: string;
  dependencies?: HealthDependencies | null;
}

export interface ErrorResponse {
  error: ErrorDetail;
}

// === SSE 스트리밍 이벤트 타입 ===

export interface SessionEvent {
  type: 'session';
  session_id: string;
}

export interface StatusEvent {
  type: 'status';
  status: QueryRequestStatus;
  message?: string | null;
}

export interface QueryPreviewEvent {
  type: 'query_preview';
  query: string;
  explanation: string;
}

export interface ConfirmRequiredEvent {
  type: 'confirm_required';
  query_id: string;
}

export interface ConfirmationRequiredEvent {
  type: 'confirmation_required';
  query_id: string;
  query: string;
  explanation: string;
}

export interface ResultEvent {
  type: 'result';
  data: QueryResultData;
}

export interface ErrorEvent {
  type: 'error';
  error: ErrorDetail;
}

export interface DoneEvent {
  type: 'done';
  awaiting_confirmation: boolean;
}

// SSE 이벤트 유니온 타입
export type ChatStreamEvent =
  | SessionEvent
  | StatusEvent
  | QueryPreviewEvent
  | ConfirmRequiredEvent
  | ConfirmationRequiredEvent
  | ResultEvent
  | ErrorEvent
  | DoneEvent;

// === 스키마 관련 타입 ===

export interface ForeignKeyInfo {
  referenced_table: string;
  referenced_column: string;
}

export interface SchemaColumnInfo {
  name: string;
  data_type: string;
  is_nullable: boolean;
  description?: string | null;
  default_value?: string | null;
  is_primary_key: boolean;
  foreign_key_reference?: ForeignKeyInfo | null;
}

export interface TableInfo {
  name: string;
  description?: string | null;
  columns: SchemaColumnInfo[];
  estimated_row_count: number;
}

export interface DatabaseSchema {
  version: string;
  last_updated_at: string;
  tables: TableInfo[];
}

// === UI 상태 타입 ===

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: Date;
  queryPreview?: {
    query: string;
    explanation: string;
    queryId: string;
  };
  queryResult?: QueryResultData;
  error?: ErrorDetail;
  isLoading?: boolean;
}

export interface ChatState {
  messages: ChatMessage[];
  isLoading: boolean;
  currentStatus: QueryRequestStatus | null;
  awaitingConfirmation: boolean;
  pendingQueryId: string | null;
  error: ErrorDetail | null;
}
