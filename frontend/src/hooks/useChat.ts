/**
 * useChat 훅
 *
 * SSE 스트리밍 처리가 포함된 채팅 관리 훅입니다.
 * 메시지 전송, 쿼리 확인, 상태 관리를 담당합니다.
 */

import { useState, useCallback, useRef } from 'react';
import { v4 as uuidv4 } from 'uuid';
import type {
  ChatMessage,
  ChatState,
  QueryRequestStatus,
  QueryResultData,
  ErrorDetail,
  LLMProvider,
} from '../types';
import { api, streamChat, ApiError } from '../services/api';

export interface UseChatOptions {
  /** 세션 ID */
  sessionId?: string | null;
  /** LLM 제공자 */
  llmProvider?: LLMProvider;
  /** 세션 ID 설정 콜백 (SSE에서 받은 세션 ID 저장용) */
  onSessionId?: (sessionId: string) => void;
  /** 확인 필요 시 콜백 */
  onConfirmationRequired?: (queryId: string, query: string, explanation: string) => void;
}

export interface UseChatReturn {
  /** 채팅 상태 */
  state: ChatState;
  /** 메시지 목록 */
  messages: ChatMessage[];
  /** 로딩 중 */
  isLoading: boolean;
  /** 현재 상태 */
  currentStatus: QueryRequestStatus | null;
  /** 확인 대기 중 */
  awaitingConfirmation: boolean;
  /** 대기 중인 쿼리 ID */
  pendingQueryId: string | null;
  /** 에러 */
  error: ErrorDetail | null;
  /** 메시지 전송 */
  sendMessage: (message: string) => Promise<void>;
  /** 쿼리 확인 (승인/거부) */
  confirmQuery: (approved: boolean) => Promise<void>;
  /** 요청 취소 */
  cancelRequest: () => void;
  /** 채팅 초기화 */
  clearChat: () => void;
  /** 에러 초기화 */
  clearError: () => void;
}

/**
 * 초기 채팅 상태
 */
const initialState: ChatState = {
  messages: [],
  isLoading: false,
  currentStatus: null,
  awaitingConfirmation: false,
  pendingQueryId: null,
  error: null,
};

/**
 * 채팅 관리 훅
 */
export function useChat(options: UseChatOptions = {}): UseChatReturn {
  const { sessionId, llmProvider = 'openai', onSessionId, onConfirmationRequired } = options;

  const [state, setState] = useState<ChatState>(initialState);
  const abortControllerRef = useRef<AbortController | null>(null);
  const currentSessionIdRef = useRef<string | null>(sessionId || null);

  // sessionId가 변경되면 ref 업데이트
  if (sessionId !== currentSessionIdRef.current) {
    currentSessionIdRef.current = sessionId || null;
  }

  /**
   * 메시지 추가
   */
  const addMessage = useCallback((message: Omit<ChatMessage, 'id' | 'timestamp'>) => {
    const newMessage: ChatMessage = {
      ...message,
      id: uuidv4(),
      timestamp: new Date(),
    };

    setState((prev) => ({
      ...prev,
      messages: [...prev.messages, newMessage],
    }));

    return newMessage.id;
  }, []);

  /**
   * 메시지 업데이트
   */
  const updateMessage = useCallback(
    (messageId: string, updates: Partial<ChatMessage>) => {
      setState((prev) => ({
        ...prev,
        messages: prev.messages.map((msg) =>
          msg.id === messageId ? { ...msg, ...updates } : msg
        ),
      }));
    },
    []
  );

  /**
   * 메시지 전송
   */
  const sendMessage = useCallback(
    async (message: string): Promise<void> => {
      if (!message.trim()) return;

      // 이전 요청 취소
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }

      // 새 AbortController 생성
      abortControllerRef.current = new AbortController();

      // 사용자 메시지 추가
      addMessage({
        role: 'user',
        content: message,
      });

      // 어시스턴트 로딩 메시지 추가
      const assistantMessageId = addMessage({
        role: 'assistant',
        content: '',
        isLoading: true,
      });

      // 상태 초기화
      setState((prev) => ({
        ...prev,
        isLoading: true,
        currentStatus: 'pending',
        awaitingConfirmation: false,
        pendingQueryId: null,
        error: null,
      }));

      let queryPreview: { query: string; explanation: string; queryId: string } | undefined;
      let queryResult: QueryResultData | undefined;

      try {
        await streamChat(
          {
            session_id: currentSessionIdRef.current,
            message,
            llm_provider: llmProvider,
          },
          {
            onSession: (event) => {
              currentSessionIdRef.current = event.session_id;
              onSessionId?.(event.session_id);
            },

            onStatus: (event) => {
              setState((prev) => ({
                ...prev,
                currentStatus: event.status,
              }));

              // 상태 메시지 업데이트
              if (event.message) {
                updateMessage(assistantMessageId, {
                  content: event.message,
                });
              }
            },

            onQueryPreview: (event) => {
              queryPreview = {
                query: event.query,
                explanation: event.explanation,
                queryId: '', // confirm_required에서 설정됨
              };
            },

            onConfirmRequired: (event) => {
              if (queryPreview) {
                queryPreview.queryId = event.query_id;
              }

              setState((prev) => ({
                ...prev,
                awaitingConfirmation: true,
                pendingQueryId: event.query_id,
              }));
            },

            onConfirmationRequired: (event) => {
              queryPreview = {
                query: event.query,
                explanation: event.explanation,
                queryId: event.query_id,
              };

              setState((prev) => ({
                ...prev,
                awaitingConfirmation: true,
                pendingQueryId: event.query_id,
              }));

              onConfirmationRequired?.(event.query_id, event.query, event.explanation);
            },

            onResult: (event) => {
              queryResult = event.data;
            },

            onError: (event) => {
              setState((prev) => ({
                ...prev,
                error: event.error,
              }));

              updateMessage(assistantMessageId, {
                content: event.error.message,
                error: event.error,
                isLoading: false,
              });
            },

            onDone: (event) => {
              // 최종 메시지 업데이트
              updateMessage(assistantMessageId, {
                content: queryResult
                  ? `쿼리가 실행되었습니다. ${queryResult.returned_row_count}개의 결과가 있습니다.`
                  : queryPreview
                    ? queryPreview.explanation
                    : '',
                queryPreview: queryPreview,
                queryResult: queryResult,
                isLoading: false,
              });

              setState((prev) => ({
                ...prev,
                isLoading: false,
                currentStatus: event.awaiting_confirmation ? 'awaiting_confirm' : 'completed',
                awaitingConfirmation: event.awaiting_confirmation,
              }));
            },

            onConnectionError: (error) => {
              console.error('SSE 연결 오류:', error);
            },
          },
          abortControllerRef.current.signal
        );
      } catch (error) {
        const errorDetail: ErrorDetail =
          error instanceof ApiError
            ? { code: error.code, message: error.message }
            : { code: 'UNKNOWN_ERROR', message: '알 수 없는 오류가 발생했습니다.' };

        setState((prev) => ({
          ...prev,
          isLoading: false,
          currentStatus: 'failed',
          error: errorDetail,
        }));

        updateMessage(assistantMessageId, {
          content: errorDetail.message,
          error: errorDetail,
          isLoading: false,
        });
      } finally {
        abortControllerRef.current = null;
      }
    },
    [addMessage, updateMessage, llmProvider, onSessionId, onConfirmationRequired]
  );

  /**
   * 쿼리 확인 (승인/거부)
   */
  const confirmQuery = useCallback(
    async (approved: boolean): Promise<void> => {
      const queryId = state.pendingQueryId;
      const currentSessionId = currentSessionIdRef.current;

      if (!queryId || !currentSessionId) {
        console.error('확인할 쿼리가 없습니다.');
        return;
      }

      setState((prev) => ({
        ...prev,
        isLoading: true,
        currentStatus: approved ? 'executing' : 'cancelled',
      }));

      try {
        const response = await api.confirmQuery({
          session_id: currentSessionId,
          query_id: queryId,
          approved,
        });

        if (response.success && response.result) {
          // 마지막 어시스턴트 메시지에 결과 추가
          const lastAssistantMessage = state.messages
            .filter((m) => m.role === 'assistant')
            .pop();

          if (lastAssistantMessage) {
            updateMessage(lastAssistantMessage.id, {
              queryResult: response.result,
              content: `쿼리가 실행되었습니다. ${response.result.returned_row_count}개의 결과가 있습니다.`,
            });
          }

          setState((prev) => ({
            ...prev,
            isLoading: false,
            currentStatus: 'completed',
            awaitingConfirmation: false,
            pendingQueryId: null,
          }));
        } else if (response.error) {
          setState((prev) => ({
            ...prev,
            isLoading: false,
            currentStatus: 'failed',
            awaitingConfirmation: false,
            pendingQueryId: null,
            error: response.error,
          }));
        } else {
          // 취소된 경우
          setState((prev) => ({
            ...prev,
            isLoading: false,
            currentStatus: 'cancelled',
            awaitingConfirmation: false,
            pendingQueryId: null,
          }));

          // 취소 메시지 추가
          addMessage({
            role: 'assistant',
            content: '쿼리 실행이 취소되었습니다.',
          });
        }
      } catch (error) {
        const errorDetail: ErrorDetail =
          error instanceof ApiError
            ? { code: error.code, message: error.message }
            : { code: 'CONFIRM_ERROR', message: '쿼리 확인 중 오류가 발생했습니다.' };

        setState((prev) => ({
          ...prev,
          isLoading: false,
          currentStatus: 'failed',
          awaitingConfirmation: false,
          pendingQueryId: null,
          error: errorDetail,
        }));
      }
    },
    [state.pendingQueryId, state.messages, updateMessage, addMessage]
  );

  /**
   * 요청 취소
   */
  const cancelRequest = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }

    setState((prev) => ({
      ...prev,
      isLoading: false,
      currentStatus: 'cancelled',
    }));
  }, []);

  /**
   * 채팅 초기화
   */
  const clearChat = useCallback(() => {
    cancelRequest();
    setState(initialState);
  }, [cancelRequest]);

  /**
   * 에러 초기화
   */
  const clearError = useCallback(() => {
    setState((prev) => ({
      ...prev,
      error: null,
    }));
  }, []);

  return {
    state,
    messages: state.messages,
    isLoading: state.isLoading,
    currentStatus: state.currentStatus,
    awaitingConfirmation: state.awaitingConfirmation,
    pendingQueryId: state.pendingQueryId,
    error: state.error,
    sendMessage,
    confirmQuery,
    cancelRequest,
    clearChat,
    clearError,
  };
}

export default useChat;
