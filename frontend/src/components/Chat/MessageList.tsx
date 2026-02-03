/**
 * 메시지 목록 컴포넌트
 *
 * 채팅 메시지들을 표시하고 자동 스크롤을 지원합니다.
 */

import { useRef, useEffect } from "react";
import type { ChatMessage, QueryResultData } from "../../types";
import { QueryPreview } from "./QueryPreview";
import { ErrorMessage } from "../common/ErrorMessage";
import { StatusSpinner } from "../common/LoadingSpinner";

interface MessageListProps {
  /** 메시지 목록 */
  messages: ChatMessage[];
  /** 쿼리 승인 핸들러 */
  onApproveQuery?: (queryId: string) => void;
  /** 로딩 상태 */
  isLoading?: boolean;
  /** 현재 상태 */
  currentStatus?: string | null;
  /** 예시 질문 선택 핸들러 */
  onExampleSelect?: (query: string) => void;
  /** 결과 선택 콜백 (우측 패널에 표시) */
  onSelectResult?: (result: QueryResultData, query: string) => void;
}

export function MessageList({
  messages,
  onApproveQuery,
  isLoading = false,
  currentStatus,
  onExampleSelect,
  onSelectResult,
}: MessageListProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // 새 메시지 시 자동 스크롤
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, isLoading]);

  // 새 결과가 도착하면 자동으로 우측 패널에 표시
  useEffect(() => {
    if (!onSelectResult) return;
    const lastMessage = messages[messages.length - 1];
    if (lastMessage?.queryResult && lastMessage?.queryPreview?.query) {
      onSelectResult(lastMessage.queryResult, lastMessage.queryPreview.query);
    }
  }, [messages, onSelectResult]);

  const formatTime = (date: Date) => {
    return new Intl.DateTimeFormat("ko-KR", {
      hour: "2-digit",
      minute: "2-digit",
    }).format(date);
  };

  const exampleQueries = [
    "지난달 매출 상위 10개 제품은?",
    "재고가 부족한 창고 목록을 보여줘",
    "이번 분기 총 주문 건수는?",
  ];

  if (messages.length === 0) {
    return (
      <div className="flex h-full flex-col items-center justify-center text-center px-4 pt-16 animate-fade-in">
        {/* 아이콘 영역 */}
        <div className="relative mb-6">
          {/* 배경 글로우 */}
          <div className="absolute inset-0 bg-gradient-to-r from-primary-600/20 to-accent-500/20 rounded-full blur-2xl scale-150"></div>

          {/* 메인 아이콘 */}
          <div className="relative rounded-2xl bg-gradient-to-br from-primary-600 to-accent-600 p-5 shadow-glow-mixed animate-float">
            <svg
              className="h-10 w-10 text-white"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4"
              />
            </svg>
          </div>
        </div>

        <h3 className="text-xl font-bold bg-gradient-to-r from-primary-600 to-accent-500 bg-clip-text text-transparent drop-shadow-md">
          자연어로 데이터베이스 질의하기
        </h3>
        <p className="mt-2 max-w-sm text-sm text-white font-medium">
          궁금한 것을 자연어로 물어보세요. SQL 쿼리로 변환해 결과를
          보여드립니다.
        </p>

        {/* 예시 질문 버튼들 */}
        <div className="mt-8 space-y-2 w-full max-w-md">
          <p className="text-xs text-gray-100 font-medium mb-3">
            예시 질문을 클릭해보세요
          </p>
          {exampleQueries.map((example, index) => (
            <button
              key={index}
              className="w-full text-left px-4 py-3 rounded-xl bg-white/60 border border-gray-300 text-black text-sm font-medium hover:bg-white/80 hover:border-primary-500/50 hover:-translate-y-0.5 hover:shadow-md transition-all duration-200"
              onClick={() => onExampleSelect?.(example)}
            >
              "{example}"
            </button>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      className="h-full space-y-4 overflow-y-auto p-4 scrollbar-dark"
    >
      {messages.map((message) => (
        <div
          key={message.id}
          className={`flex ${message.role === "user" ? "justify-end" : "justify-start"} ${
            message.role === "user"
              ? "animate-slide-in-right"
              : "animate-slide-in-left"
          }`}
        >
          <div
            className={`max-w-[85%] px-4 py-3 ${
              message.role === "user" ? "message-user" : "message-ai pl-6"
            }`}
          >
            {/* 메시지 내용 */}
            {message.isLoading ? (
              <StatusSpinner
                status={
                  (currentStatus as
                    | "pending"
                    | "generating"
                    | "validating"
                    | "executing") || "pending"
                }
              />
            ) : (
              <>
                {message.content && (
                  <p className="whitespace-pre-wrap text-sm">
                    {message.content}
                  </p>
                )}

                {/* 에러 표시 */}
                {message.error && (
                  <div className="mt-3">
                    <ErrorMessage
                      code={message.error.code}
                      message={message.error.message}
                      severity={
                        message.error.code === "DANGEROUS_QUERY"
                          ? "warning"
                          : message.error.code === "EMPTY_RESULT"
                            ? "info"
                            : "error"
                      }
                    />
                  </div>
                )}

                {/* 쿼리 미리보기 - 결과가 없을 때 (실행 버튼 표시) */}
                {message.queryPreview &&
                  !message.queryResult &&
                  onApproveQuery && (
                    <div className="mt-3">
                      <QueryPreview
                        queryId={message.queryPreview.queryId}
                        query={message.queryPreview.query}
                        explanation={message.queryPreview.explanation}
                        onApprove={onApproveQuery}
                        isLoading={isLoading}
                      />
                    </div>
                  )}

                {/* 쿼리 미리보기 - 결과가 있을 때 (결과 보기 버튼 표시) */}
                {message.queryPreview && message.queryResult && (
                  <div className="mt-3">
                    <div className="code-block">
                      <pre className="overflow-x-auto text-xs">
                        <code className="text-emerald-400">
                          {message.queryPreview.query}
                        </code>
                      </pre>
                    </div>
                    <div className="flex items-center justify-between mt-3">
                      <span className="text-xs text-content-tertiary">
                        {message.queryResult.returned_row_count}개 행 반환
                      </span>
                      <button
                        onClick={() =>
                          onSelectResult?.(
                            message.queryResult!,
                            message.queryPreview!.query,
                          )
                        }
                        className="btn-primary flex items-center gap-2 text-sm"
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
                            d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                          />
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
                          />
                        </svg>
                        결과 보기
                      </button>
                    </div>
                  </div>
                )}
              </>
            )}

            {/* 타임스탬프 */}
            <p
              className={`mt-2 text-xs ${
                message.role === "user"
                  ? "text-primary-200"
                  : "text-content-tertiary"
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
