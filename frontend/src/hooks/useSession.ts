/**
 * useSession 훅
 *
 * 세션 관리를 위한 React 훅입니다.
 * 로컬 스토리지에 세션 ID를 저장하고, 세션 생성/조회/종료를 관리합니다.
 */

import { useState, useEffect, useCallback } from 'react';
import type { SessionResponse, LLMProvider } from '../types';
import { api, ApiError } from '../services/api';

const SESSION_STORAGE_KEY = 'text2sql_session_id';

export interface UseSessionOptions {
  /** 자동으로 세션 복구 시도 */
  autoRestore?: boolean;
  /** 기본 LLM 제공자 */
  defaultLLMProvider?: LLMProvider;
}

export interface UseSessionReturn {
  /** 현재 세션 정보 */
  session: SessionResponse | null;
  /** 세션 ID */
  sessionId: string | null;
  /** 세션 로딩 중 */
  isLoading: boolean;
  /** 에러 정보 */
  error: Error | null;
  /** 새 세션 생성 */
  createNewSession: (llmProvider?: LLMProvider) => Promise<SessionResponse>;
  /** 기존 세션 복구 */
  restoreSession: (sessionId: string) => Promise<SessionResponse | null>;
  /** 세션 종료 */
  terminateSession: () => Promise<void>;
  /** 세션 초기화 (로컬 상태만) */
  clearSession: () => void;
  /** 세션 ID 설정 (외부에서 설정할 때) */
  setSessionId: (sessionId: string) => void;
}

/**
 * 세션 관리 훅
 */
export function useSession(options: UseSessionOptions = {}): UseSessionReturn {
  const { autoRestore = true, defaultLLMProvider = 'openai' } = options;

  const [session, setSession] = useState<SessionResponse | null>(null);
  const [sessionId, setSessionIdState] = useState<string | null>(() => {
    // 초기값은 로컬 스토리지에서 가져오기
    if (typeof window !== 'undefined') {
      return localStorage.getItem(SESSION_STORAGE_KEY);
    }
    return null;
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  /**
   * 세션 ID를 로컬 스토리지에 저장
   */
  const saveSessionId = useCallback((id: string | null) => {
    setSessionIdState(id);
    if (typeof window !== 'undefined') {
      if (id) {
        localStorage.setItem(SESSION_STORAGE_KEY, id);
      } else {
        localStorage.removeItem(SESSION_STORAGE_KEY);
      }
    }
  }, []);

  /**
   * 세션 ID 설정 (외부에서 설정할 때)
   */
  const setSessionId = useCallback(
    (id: string) => {
      saveSessionId(id);
    },
    [saveSessionId]
  );

  /**
   * 새 세션 생성
   */
  const createNewSession = useCallback(
    async (llmProvider: LLMProvider = defaultLLMProvider): Promise<SessionResponse> => {
      setIsLoading(true);
      setError(null);

      try {
        const newSession = await api.createSession({ llm_provider: llmProvider });
        setSession(newSession);
        saveSessionId(newSession.session_id);
        return newSession;
      } catch (err) {
        const error = err instanceof Error ? err : new Error('세션 생성 실패');
        setError(error);
        throw error;
      } finally {
        setIsLoading(false);
      }
    },
    [defaultLLMProvider, saveSessionId]
  );

  /**
   * 기존 세션 복구
   */
  const restoreSession = useCallback(
    async (id: string): Promise<SessionResponse | null> => {
      setIsLoading(true);
      setError(null);

      try {
        const existingSession = await api.getSession(id);

        // 만료된 세션이면 null 반환
        if (existingSession.status === 'expired' || existingSession.status === 'terminated') {
          saveSessionId(null);
          setSession(null);
          return null;
        }

        setSession(existingSession);
        saveSessionId(existingSession.session_id);
        return existingSession;
      } catch (err) {
        // 세션을 찾을 수 없으면 로컬 스토리지 정리
        if (err instanceof ApiError && err.status === 404) {
          saveSessionId(null);
          setSession(null);
          return null;
        }

        const error = err instanceof Error ? err : new Error('세션 복구 실패');
        setError(error);
        throw error;
      } finally {
        setIsLoading(false);
      }
    },
    [saveSessionId]
  );

  /**
   * 세션 종료
   */
  const terminateSession = useCallback(async (): Promise<void> => {
    if (!sessionId) return;

    setIsLoading(true);
    setError(null);

    try {
      await api.terminateSession(sessionId);
    } catch {
      // 이미 종료된 세션이어도 무시
    } finally {
      setSession(null);
      saveSessionId(null);
      setIsLoading(false);
    }
  }, [sessionId, saveSessionId]);

  /**
   * 세션 초기화 (로컬 상태만)
   */
  const clearSession = useCallback(() => {
    setSession(null);
    saveSessionId(null);
    setError(null);
  }, [saveSessionId]);

  /**
   * 자동 세션 복구
   */
  useEffect(() => {
    if (autoRestore && sessionId && !session) {
      restoreSession(sessionId).catch(() => {
        // 복구 실패 시 조용히 처리 (에러는 이미 상태에 저장됨)
      });
    }
  }, [autoRestore, sessionId, session, restoreSession]);

  return {
    session,
    sessionId,
    isLoading,
    error,
    createNewSession,
    restoreSession,
    terminateSession,
    clearSession,
    setSessionId,
  };
}

export default useSession;
