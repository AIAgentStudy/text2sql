/**
 * 메시지 목록 컴포넌트
 *
 * 채팅 메시지들을 표시하고 자동 스크롤을 지원합니다.
 */

import { useRef, useEffect } from 'react';
import type { ChatMessage } from '../../types';
import { QueryPreview } from './QueryPreview';
import { ResultTable } from './ResultTable';
import { ErrorMessage } from '../common/ErrorMessage';
import { StatusSpinner } from '../common/LoadingSpinner';

interface MessageListProps {
  /** 메시지 목록 */
  messages: ChatMessage[];
  /** 확인 대기 중인 쿼리 ID */
  pendingQueryId?: string | null;
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
  pendingQueryId,
  onApproveQuery,
  onRejectQuery,
  isLoading = false,
  currentStatus,
}: MessageListProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

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

  if (messages.length === 0) {
    return (
      <div className="flex h-full flex-col items-center justify-center text-center">
        <div className="mb-4 rounded-full bg-blue-100 p-4">
          <svg
            className="h-8 w-8 text-blue-600"
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
        <h3 className="text-lg font-medium text-gray-900">대화를 시작하세요</h3>
        <p className="mt-2 max-w-sm text-sm text-gray-500">
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
      className="flex-1 space-y-4 overflow-y-auto p-4"
    >
      {messages.map((message) => (
        <div
          key={message.id}
          className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
        >
          <div
            className={`max-w-[85%] rounded-lg px-4 py-3 ${
              message.role === 'user'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-900'
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

                {/* 쿼리 미리보기 (확인 대기 중일 때만) */}
                {message.queryPreview &&
                  pendingQueryId === message.queryPreview.queryId &&
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

                {/* 이미 실행된 쿼리 미리보기 (읽기 전용) */}
                {message.queryPreview &&
                  pendingQueryId !== message.queryPreview.queryId &&
                  message.queryResult && (
                    <div className="mt-3">
                      <div className="rounded-md bg-gray-800 p-3">
                        <pre className="overflow-x-auto text-xs text-green-400">
                          <code>{message.queryPreview.query}</code>
                        </pre>
                      </div>
                    </div>
                  )}

                {/* 쿼리 결과 */}
                {message.queryResult && (
                  <div className="mt-3">
                    <ResultTable data={message.queryResult} />
                  </div>
                )}
              </>
            )}

            {/* 타임스탬프 */}
            <p
              className={`mt-2 text-xs ${
                message.role === 'user' ? 'text-blue-200' : 'text-gray-400'
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
