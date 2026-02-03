/**
 * 메시지 목록 컴포넌트
 *
 * 채팅 메시지들을 표시하고 자동 스크롤을 지원합니다.
 */

import { useRef, useEffect, useState } from 'react';
import type { ChatMessage } from '../../types';
import { QueryPreview } from './QueryPreview';
import { ResultTable } from './ResultTable';
import { ErrorMessage } from '../common/ErrorMessage';
import { StatusSpinner } from '../common/LoadingSpinner';

interface MessageListProps {
  /** 메시지 목록 */
  messages: ChatMessage[];
  /** 쿼리 승인 핸들러 */
  onApproveQuery?: (queryId: string, modifiedQuery?: string) => void;
  /** 쿼리 거부 핸들러 */
  onRejectQuery?: (queryId: string) => void;
  /** 로딩 상태 */
  isLoading?: boolean;
  /** 현재 상태 */
  currentStatus?: string | null;
}

export function MessageList({
  messages,
  onApproveQuery,
  onRejectQuery,
  isLoading = false,
  currentStatus,
}: MessageListProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  // 각 메시지별로 결과 표시 여부를 관리
  const [visibleResults, setVisibleResults] = useState<Record<string, boolean>>({});

  // 새 메시지 시 자동 스크롤
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isLoading]);

  const formatTime = (date: Date) => {
    return new Intl.DateTimeFormat('ko-KR', {
      hour: '2-digit',
      minute: '2-digit',
    }).format(date);
  };

  const toggleResult = (messageId: string) => {
    setVisibleResults(prev => ({
      ...prev,
      [messageId]: !prev[messageId]
    }));
  };

  if (messages.length === 0) {
    return (
      <div className="flex h-full flex-col items-center justify-center text-center px-4 pt-16">
        <div className="mb-4 rounded-full bg-gradient-to-r from-primary-600 to-primary-700 p-4 shadow-lg shadow-primary-900/30">
          <svg
            className="h-8 w-8 text-white"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
            />
          </svg>
        </div>
        <h3 className="text-lg font-medium text-content-primary">대화를 시작하세요</h3>
        <p className="mt-2 max-w-sm text-sm text-content-secondary">
          자연어로 데이터베이스에 질문해보세요.
          <br />
          예: "지난달 매출 상위 10개 제품이 뭐야?"
        </p>
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      className="flex-1 space-y-4 overflow-y-auto p-4 scrollbar-dark"
    >
      {messages.map((message) => (
        <div
          key={message.id}
          className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
        >
          <div
            className={`max-w-[85%] px-4 py-3 ${
              message.role === 'user'
                ? 'message-user'
                : 'message-ai'
            }`}
          >
            {/* 메시지 내용 */}
            {message.isLoading ? (
              <StatusSpinner
                status={
                  (currentStatus as 'pending' | 'generating' | 'validating' | 'executing') || 'pending'
                }
              />
            ) : (
              <>
                {message.content && (
                  <p className="whitespace-pre-wrap text-sm">{message.content}</p>
                )}

                {/* 에러 표시 */}
                {message.error && (
                  <div className="mt-3">
                    <ErrorMessage
                      code={message.error.code}
                      message={message.error.message}
                      severity={
                        message.error.code === 'DANGEROUS_QUERY'
                          ? 'warning'
                          : message.error.code === 'EMPTY_RESULT'
                          ? 'info'
                          : 'error'
                      }
                    />
                  </div>
                )}

                {/* 쿼리 미리보기 - 결과가 없을 때 (실행/취소 버튼 표시) */}
                {message.queryPreview &&
                  !message.queryResult &&
                  onApproveQuery &&
                  onRejectQuery && (
                    <div className="mt-3">
                      <QueryPreview
                        queryId={message.queryPreview.queryId}
                        query={message.queryPreview.query}
                        explanation={message.queryPreview.explanation}
                        onApprove={onApproveQuery}
                        onReject={onRejectQuery}
                        isLoading={isLoading}
                      />
                    </div>
                  )}

                {/* 쿼리 미리보기 - 결과가 있을 때 (결과 보기 버튼 표시) */}
                {message.queryPreview && message.queryResult && (
                  <div className="mt-3">
                    <div className="code-block">
                      <pre className="overflow-x-auto text-xs">
                        <code className="text-emerald-400">{message.queryPreview.query}</code>
                      </pre>
                    </div>
                    <div className="flex justify-end mt-3">
                      <button
                        onClick={() => toggleResult(message.id)}
                        className="btn-primary flex items-center gap-2"
                      >
                        {visibleResults[message.id] ? (
                          <>
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                            </svg>
                            결과 숨기기
                          </>
                        ) : (
                          <>
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                            </svg>
                            결과 보기
                          </>
                        )}
                      </button>
                    </div>
                  </div>
                )}

                {/* 쿼리 결과 (실행 버튼을 누른 후에만 표시) */}
                {message.queryResult && visibleResults[message.id] && (
                  <div className="mt-3">
                    <ResultTable data={message.queryResult} />
                  </div>
                )}
              </>
            )}

            {/* 타임스탬프 */}
            <p
              className={`mt-2 text-xs ${
                message.role === 'user' ? 'text-primary-200' : 'text-content-tertiary'
              }`}
            >
              {formatTime(message.timestamp)}
            </p>
          </div>
        </div>
      ))}

      <div ref={messagesEndRef} />
    </div>
  );
}

export default MessageList;
