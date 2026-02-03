/**
 * 채팅 컨테이너 컴포넌트
 *
 * 채팅 UI의 메인 컨테이너로, 메시지 목록과 입력창을 포함합니다.
 * useSession과 useChat 훅을 사용하여 상태를 관리합니다.
 */

import { useCallback, useState } from 'react';
import { MessageList } from './MessageList';
import { MessageInput } from './MessageInput';
import { useSession } from '../../hooks/useSession';
import { useChat } from '../../hooks/useChat';
import type { LLMProvider } from '../../types';

const LLM_PROVIDERS: { value: LLMProvider; label: string }[] = [
  { value: 'openai', label: 'OpenAI' },
  { value: 'anthropic', label: 'Anthropic' },
  { value: 'google', label: 'Google' },
];

interface ChatContainerProps {
  /** LLM 제공자 */
  llmProvider?: LLMProvider;
}

export function ChatContainer({ llmProvider = 'openai' }: ChatContainerProps) {
  const [selectedProvider, setSelectedProvider] = useState<LLMProvider>(llmProvider);

  const {
    sessionId,
    setSessionId,
    terminateSession,
  } = useSession({
    autoRestore: true,
    defaultLLMProvider: selectedProvider,
  });

  const {
    messages,
    isLoading,
    currentStatus,
    awaitingConfirmation,
    sendMessage,
    confirmQuery,
    clearChat,
  } = useChat({
    sessionId,
    llmProvider: selectedProvider,
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
    <div className="flex h-full min-h-[500px] flex-col card overflow-hidden">
      {/* 헤더 */}
      <div className="flex items-center justify-between border-b border-surface-border px-4 py-3 bg-dark-800/50">
        <div className="flex items-center gap-3">
          <div
            className={`h-2.5 w-2.5 rounded-full ${
              sessionId
                ? 'bg-emerald-500 shadow-lg shadow-emerald-500/50'
                : 'bg-content-muted'
            }`}
          />
          <span className="text-sm text-white font-medium">
            {sessionId ? '세션 연결됨' : '세션 대기 중'}
          </span>
        </div>
        <div className="flex items-center gap-4">
          <select
            value={selectedProvider}
            onChange={(e) => setSelectedProvider(e.target.value as LLMProvider)}
            disabled={isLoading}
            className="bg-dark-700 border border-surface-border text-white rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/30 disabled:opacity-50"
          >
            {LLM_PROVIDERS.map((provider) => (
              <option key={provider.value} value={provider.value}>
                {provider.label}
              </option>
            ))}
          </select>
          <button
            onClick={handleNewChat}
            className="text-sm text-white font-medium hover:text-primary-300 transition-colors duration-200 px-3 py-1.5 rounded-lg hover:bg-surface-hover"
          >
            새 대화
          </button>
        </div>
      </div>

      {/* 메시지 목록 */}
      <div className="min-h-0 flex-1 overflow-hidden">
        <MessageList
          messages={messages}
          onApproveQuery={handleApproveQuery}
          onRejectQuery={handleRejectQuery}
          isLoading={isLoading}
          currentStatus={currentStatus}
        />
      </div>

      {/* 입력창 */}
      <div className="border-t border-surface-border p-4">
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
