/**
 * 채팅 컨테이너 컴포넌트
 *
 * 채팅 UI의 메인 컨테이너로, 메시지 목록과 입력창을 포함합니다.
 * useSession과 useChat 훅을 사용하여 상태를 관리합니다.
 */

import { useCallback } from 'react';
import { MessageList } from './MessageList';
import { MessageInput } from './MessageInput';
import { useSession } from '../../hooks/useSession';
import { useChat } from '../../hooks/useChat';
import type { LLMProvider } from '../../types';

interface ChatContainerProps {
  /** LLM 제공자 */
  llmProvider?: LLMProvider;
}

export function ChatContainer({ llmProvider = 'openai' }: ChatContainerProps) {
  const {
    sessionId,
    setSessionId,
    terminateSession,
  } = useSession({
    autoRestore: true,
    defaultLLMProvider: llmProvider,
  });

  const {
    messages,
    isLoading,
    currentStatus,
    awaitingConfirmation,
    pendingQueryId,
    sendMessage,
    confirmQuery,
    clearChat,
  } = useChat({
    sessionId,
    llmProvider,
    onSessionId: setSessionId,
  });

  const handleApproveQuery = useCallback(
    (queryId: string, _modifiedQuery?: string) => {
      // modifiedQuery 기능은 향후 구현
      void queryId;
      confirmQuery(true);
    },
    [confirmQuery]
  );

  const handleRejectQuery = useCallback(
    (_queryId: string) => {
      confirmQuery(false);
    },
    [confirmQuery]
  );

  const handleNewChat = useCallback(async () => {
    clearChat();
    await terminateSession();
  }, [clearChat, terminateSession]);

  return (
    <div className="flex h-full flex-col">
      {/* 헤더 */}
      <div className="flex items-center justify-between border-b border-gray-200 px-4 py-3">
        <div className="flex items-center gap-2">
          <div
            className={`h-2 w-2 rounded-full ${
              sessionId ? 'bg-green-500' : 'bg-gray-300'
            }`}
          />
          <span className="text-sm text-gray-600">
            {sessionId ? '세션 연결됨' : '세션 대기 중'}
          </span>
        </div>
        <button
          onClick={handleNewChat}
          className="text-sm text-gray-500 hover:text-gray-700"
        >
          새 대화
        </button>
      </div>

      {/* 메시지 목록 */}
      <div className="min-h-0 flex-1 overflow-hidden">
        <MessageList
          messages={messages}
          pendingQueryId={pendingQueryId}
          onApproveQuery={awaitingConfirmation ? handleApproveQuery : undefined}
          onRejectQuery={awaitingConfirmation ? handleRejectQuery : undefined}
          isLoading={isLoading}
          currentStatus={currentStatus}
        />
      </div>

      {/* 입력창 */}
      <div className="border-t border-gray-200 p-4">
        <MessageInput
          onSend={sendMessage}
          disabled={awaitingConfirmation}
          isLoading={isLoading}
          placeholder={
            awaitingConfirmation
              ? '쿼리 실행 여부를 먼저 선택해주세요.'
              : '자연어로 질문해보세요. 예: "지난달 매출 상위 10개 제품이 뭐야?"'
          }
        />
      </div>
    </div>
  );
}

export default ChatContainer;
