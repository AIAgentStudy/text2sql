/**
 * 메시지 입력 컴포넌트
 *
 * 사용자가 자연어 질문을 입력할 수 있는 텍스트 입력 UI를 제공합니다.
 */

import { useState, useRef, useEffect, KeyboardEvent, FormEvent } from "react";

interface MessageInputProps {
  /** 메시지 전송 핸들러 */
  onSend: (message: string) => void;
  /** 전송 가능 여부 */
  disabled?: boolean;
  /** 로딩 상태 */
  isLoading?: boolean;
  /** 플레이스홀더 텍스트 */
  placeholder?: string;
  /** 자동 포커스 */
  autoFocus?: boolean;
}

export function MessageInput({
  onSend,
  disabled = false,
  isLoading = false,
  placeholder = '자연어로 질문해보세요. 예: "지난달 매출 상위 10개 제품이 뭐야?"',
  autoFocus = true,
}: MessageInputProps) {
  const [message, setMessage] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // 자동 포커스
  useEffect(() => {
    if (autoFocus && textareaRef.current) {
      textareaRef.current.focus();
    }
  }, [autoFocus]);

  // 텍스트 영역 높이 자동 조절
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 150)}px`;
    }
  }, [message]);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (message.trim() && !disabled && !isLoading) {
      onSend(message.trim());
      setMessage("");
      // 높이 초기화
      if (textareaRef.current) {
        textareaRef.current.style.height = "auto";
      }
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    // Enter로 전송 (Shift+Enter는 줄바꿈)
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const isDisabled = disabled || isLoading;
  const canSubmit = message.trim().length > 0 && !isDisabled;

  return (
    <form onSubmit={handleSubmit} className="relative">
      <div className="flex items-end gap-2 rounded-xl glass-light p-2 focus-within:ring-2 focus-within:ring-primary-500/30 transition-all duration-200">
        <textarea
          ref={textareaRef}
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={isDisabled}
          rows={1}
          className="min-h-[40px] flex-1 resize-none border-0 bg-transparent p-2 text-sm text-black placeholder-gray-400 focus:outline-none focus:ring-0 disabled:cursor-not-allowed disabled:opacity-50"
          aria-label="메시지 입력"
        />
        <button
          type="submit"
          disabled={!canSubmit}
          className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-lg bg-gradient-to-r from-primary-600 to-primary-700 text-white shadow-lg shadow-primary-900/30 transition-all duration-200 hover:from-primary-500 hover:to-primary-600 focus:outline-none focus:ring-2 focus:ring-primary-500/50 disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:from-primary-600 disabled:hover:to-primary-700"
          aria-label="메시지 전송"
        >
          {isLoading ? (
            <svg
              className="h-5 w-5 animate-spin"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
          ) : (
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="currentColor"
              className="h-5 w-5"
            >
              <path d="M3.478 2.405a.75.75 0 00-.926.94l2.432 7.905H13.5a.75.75 0 010 1.5H4.984l-2.432 7.905a.75.75 0 00.926.94 60.519 60.519 0 0018.445-8.986.75.75 0 000-1.218A60.517 60.517 0 003.478 2.405z" />
            </svg>
          )}
        </button>
      </div>
      <p className="mt-2 text-xs text-gray-400">
        Enter로 전송, Shift+Enter로 줄바꿈
      </p>
    </form>
  );
}

export default MessageInput;
