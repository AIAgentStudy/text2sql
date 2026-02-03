/**
 * API 서비스
 *
 * SSE 스트리밍 지원이 포함된 백엔드 API 클라이언트입니다.
 * 인증 토큰 인터셉터가 포함되어 있습니다.
 */

import type {
  ChatRequest,
  ChatStreamEvent,
  ConfirmationRequest,
  ConfirmationResponse,
  CreateSessionRequest,
  HealthResponse,
  SessionResponse,
  DatabaseSchema,
} from '../types';
import { getAuthHeader, refreshToken, clearTokens } from './auth';

// API 기본 URL (환경변수 또는 기본값)
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

/**
 * API 에러 클래스
 */
export class ApiError extends Error {
  constructor(
    public code: string,
    message: string,
    public status?: number
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

/**
 * 기본 fetch 래퍼 (인증 토큰 자동 포함)
 */
async function fetchApi<T>(
  endpoint: string,
  options: RequestInit = {},
  retry = true
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;

  const response = await fetch(url, {
    ...options,
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeader(),
      ...options.headers,
    },
  });

  // 401 에러 시 토큰 갱신 후 재시도
  if (response.status === 401 && retry) {
    const newTokens = await refreshToken();
    if (newTokens) {
      return fetchApi<T>(endpoint, options, false);
    }
    // 토큰 갱신 실패 시 로그인 페이지로 리다이렉트
    clearTokens();
    window.location.href = '/login';
    throw new ApiError('UNAUTHORIZED', '인증이 만료되었습니다.', 401);
  }

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new ApiError(
      errorData.error?.code || errorData.detail || 'UNKNOWN_ERROR',
      errorData.error?.message || errorData.detail || `HTTP ${response.status} 에러가 발생했습니다.`,
      response.status
    );
  }

  return response.json();
}

/**
 * SSE 이벤트 파서
 */
function parseSSEEvent(line: string): ChatStreamEvent | null {
  if (!line.startsWith('data: ')) {
    return null;
  }

  const data = line.slice(6); // 'data: ' 제거

  if (data === '[DONE]') {
    return null;
  }

  try {
    return JSON.parse(data) as ChatStreamEvent;
  } catch {
    console.warn('SSE 파싱 실패:', data);
    return null;
  }
}

/**
 * SSE 스트림 이벤트 핸들러 타입
 */
export interface SSEEventHandlers {
  onSession?: (event: Extract<ChatStreamEvent, { type: 'session' }>) => void;
  onStatus?: (event: Extract<ChatStreamEvent, { type: 'status' }>) => void;
  onQueryPreview?: (event: Extract<ChatStreamEvent, { type: 'query_preview' }>) => void;
  onConfirmRequired?: (event: Extract<ChatStreamEvent, { type: 'confirm_required' }>) => void;
  onConfirmationRequired?: (event: Extract<ChatStreamEvent, { type: 'confirmation_required' }>) => void;
  onResult?: (event: Extract<ChatStreamEvent, { type: 'result' }>) => void;
  onError?: (event: Extract<ChatStreamEvent, { type: 'error' }>) => void;
  onDone?: (event: Extract<ChatStreamEvent, { type: 'done' }>) => void;
  onConnectionError?: (error: Error) => void;
}

/**
 * SSE 스트림 연결 (인증 토큰 포함)
 */
export async function streamChat(
  request: ChatRequest,
  handlers: SSEEventHandlers,
  signal?: AbortSignal
): Promise<void> {
  const url = `${API_BASE_URL}/api/chat`;

  try {
    let response = await fetch(url, {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'text/event-stream',
        ...getAuthHeader(),
      },
      body: JSON.stringify(request),
      signal,
    });

    // 401 에러 시 토큰 갱신 후 재시도
    if (response.status === 401) {
      const newTokens = await refreshToken();
      if (newTokens) {
        response = await fetch(url, {
          method: 'POST',
          credentials: 'include',
          headers: {
            'Content-Type': 'application/json',
            Accept: 'text/event-stream',
            ...getAuthHeader(),
          },
          body: JSON.stringify(request),
          signal,
        });
      } else {
        clearTokens();
        window.location.href = '/login';
        throw new ApiError('UNAUTHORIZED', '인증이 만료되었습니다.', 401);
      }
    }

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new ApiError(
        errorData.error?.code || errorData.detail || 'STREAM_ERROR',
        errorData.error?.message || errorData.detail || `스트림 연결 실패: HTTP ${response.status}`,
        response.status
      );
    }

    const reader = response.body?.getReader();
    if (!reader) {
      throw new ApiError('STREAM_ERROR', '응답 스트림을 읽을 수 없습니다.');
    }

    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();

      if (done) {
        break;
      }

      buffer += decoder.decode(value, { stream: true });

      // 줄 단위로 처리
      const lines = buffer.split('\n');
      buffer = lines.pop() || ''; // 마지막 불완전한 줄은 버퍼에 유지

      for (const line of lines) {
        const trimmedLine = line.trim();
        if (!trimmedLine) continue;

        const event = parseSSEEvent(trimmedLine);
        if (!event) continue;

        // 이벤트 타입별 핸들러 호출
        switch (event.type) {
          case 'session':
            handlers.onSession?.(event);
            break;
          case 'status':
            handlers.onStatus?.(event);
            break;
          case 'query_preview':
            handlers.onQueryPreview?.(event);
            break;
          case 'confirm_required':
            handlers.onConfirmRequired?.(event);
            break;
          case 'confirmation_required':
            handlers.onConfirmationRequired?.(event);
            break;
          case 'result':
            handlers.onResult?.(event);
            break;
          case 'error':
            handlers.onError?.(event);
            break;
          case 'done':
            handlers.onDone?.(event);
            break;
        }
      }
    }
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    if (error instanceof Error) {
      if (error.name === 'AbortError') {
        // 사용자가 취소한 경우
        return;
      }
      handlers.onConnectionError?.(error);
      throw new ApiError('CONNECTION_ERROR', `연결 오류: ${error.message}`);
    }
    throw error;
  }
}

// === 세션 API ===

/**
 * 새 세션 생성
 */
export async function createSession(
  request: CreateSessionRequest = {}
): Promise<SessionResponse> {
  return fetchApi<SessionResponse>('/api/sessions', {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

/**
 * 세션 조회
 */
export async function getSession(sessionId: string): Promise<SessionResponse> {
  return fetchApi<SessionResponse>(`/api/sessions/${sessionId}`);
}

/**
 * 세션 종료
 */
export async function terminateSession(sessionId: string): Promise<void> {
  await fetchApi<void>(`/api/sessions/${sessionId}`, {
    method: 'DELETE',
  });
}

// === 쿼리 확인 API ===

/**
 * 쿼리 실행 확인/취소
 */
export async function confirmQuery(
  request: ConfirmationRequest
): Promise<ConfirmationResponse> {
  return fetchApi<ConfirmationResponse>('/api/chat/confirm', {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

// === 스키마 API ===

/**
 * 데이터베이스 스키마 조회
 */
export async function getSchema(): Promise<DatabaseSchema> {
  return fetchApi<DatabaseSchema>('/api/schema');
}

/**
 * 스키마 갱신
 */
export async function refreshSchema(): Promise<DatabaseSchema> {
  return fetchApi<DatabaseSchema>('/api/schema/refresh', {
    method: 'POST',
  });
}

// === 헬스체크 API ===

/**
 * 서버 상태 확인
 */
export async function checkHealth(): Promise<HealthResponse> {
  return fetchApi<HealthResponse>('/api/health');
}

/**
 * API 서비스 객체
 */
export const api = {
  // 채팅
  streamChat,

  // 세션
  createSession,
  getSession,
  terminateSession,

  // 쿼리 확인
  confirmQuery,

  // 스키마
  getSchema,
  refreshSchema,

  // 헬스체크
  checkHealth,
};

export default api;
