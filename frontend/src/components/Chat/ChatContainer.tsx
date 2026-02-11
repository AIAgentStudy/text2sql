/**
 * 채팅 컨테이너 컴포넌트
 *
 * 채팅 UI의 메인 컨테이너로, 메시지 목록과 입력창을 포함합니다.
 * useSession과 useChat 훅을 사용하여 상태를 관리합니다.
 */

import { useCallback, useState } from "react";
import { MessageList } from "./MessageList";
import { MessageInput } from "./MessageInput";
import { useSession } from "../../hooks/useSession";
import { useChat } from "../../hooks/useChat";
import type { LLMProvider, QueryResultData } from "../../types";

const LLM_PROVIDERS: { value: LLMProvider; label: string }[] = [
  { value: "openai", label: "OpenAI" },
  // { value: "anthropic", label: "Anthropic" },
  { value: "google", label: "Google" },
];

interface ChatContainerProps {
  /** LLM 제공자 */
  llmProvider?: LLMProvider;
  /** 결과 선택 콜백 (우측 패널에 표시) */
  onSelectResult?: (result: QueryResultData, query: string) => void;
  /** 초기화 콜백 */
  onReset?: () => void;
}

export function ChatContainer({ llmProvider = "openai", onSelectResult, onReset }: ChatContainerProps) {
  const [selectedProvider, setSelectedProvider] =
    useState<LLMProvider>(llmProvider);
  const [inputMessage, setInputMessage] = useState("");

  const { sessionId, setSessionId, terminateSession } = useSession({
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
    (queryId: string) => {
      confirmQuery(queryId, true);
    },
    [confirmQuery],
  );

  const handleRejectQuery = useCallback(
    (queryId: string) => {
      confirmQuery(queryId, false);
    },
    [confirmQuery],
  );

  const handleExampleSelect = useCallback((example: string) => {
    setInputMessage(example);
  }, []);

  const handleNewChat = useCallback(async () => {
    clearChat();
    await terminateSession();
    onReset?.();
  }, [clearChat, terminateSession, onReset]);

  return (
    <div className="flex h-full min-h-[500px] flex-col card overflow-hidden">
      {/* 헤더 */}
      <div className="flex items-center justify-between border-b border-surface-border px-4 py-3 bg-dark-800/50">
        <div className="flex items-center gap-3">
          <div
            className={`status-dot ${
              sessionId ? "status-dot-connected" : "status-dot-disconnected"
            }`}
          />
          <span className="text-sm text-content-primary font-medium">
            {sessionId ? "세션 연결됨" : "세션 대기 중"}
          </span>
          {sessionId && (
            <span className="text-xs text-content-primary font-mono">
              #{sessionId.slice(-6)}
            </span>
          )}
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
            className="btn-ghost flex items-center gap-2 text-sm"
          >
            <svg
              className="w-4 h-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 4v16m8-8H4"
              />
            </svg>
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
          onExampleSelect={handleExampleSelect}
          onSelectResult={onSelectResult}
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
              ? "쿼리 실행 여부를 먼저 선택해주세요."
              : '자연어로 질문해보세요.'
          }
          value={inputMessage}
          onChange={setInputMessage}
        />
      </div>
    </div>
  );
}

export default ChatContainer;
