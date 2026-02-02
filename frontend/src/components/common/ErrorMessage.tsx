/**
 * 에러 메시지 컴포넌트
 *
 * 다양한 오류 상황에서 사용자 친화적인 메시지를 표시합니다.
 */

import { ReactNode } from 'react';

type ErrorSeverity = 'error' | 'warning' | 'info';

interface ErrorMessageProps {
  /** 에러 코드 */
  code?: string;
  /** 에러 메시지 (한국어) */
  message: string;
  /** 추가 제안/도움말 */
  suggestion?: string;
  /** 오류 심각도 */
  severity?: ErrorSeverity;
  /** 재시도 버튼 핸들러 */
  onRetry?: () => void;
  /** 닫기 버튼 핸들러 */
  onDismiss?: () => void;
  /** 추가 컨텐츠 */
  children?: ReactNode;
}

const severityStyles: Record<ErrorSeverity, { bg: string; border: string; icon: string; text: string }> = {
  error: {
    bg: 'bg-red-500/10',
    border: 'border-red-500/20',
    icon: 'text-red-400',
    text: 'text-red-300',
  },
  warning: {
    bg: 'bg-amber-500/10',
    border: 'border-amber-500/20',
    icon: 'text-amber-400',
    text: 'text-amber-300',
  },
  info: {
    bg: 'bg-blue-500/10',
    border: 'border-blue-500/20',
    icon: 'text-blue-400',
    text: 'text-blue-300',
  },
};

const severityIcons: Record<ErrorSeverity, ReactNode> = {
  error: (
    <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
      <path
        fillRule="evenodd"
        d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
        clipRule="evenodd"
      />
    </svg>
  ),
  warning: (
    <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
      <path
        fillRule="evenodd"
        d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
        clipRule="evenodd"
      />
    </svg>
  ),
  info: (
    <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
      <path
        fillRule="evenodd"
        d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
        clipRule="evenodd"
      />
    </svg>
  ),
};

export function ErrorMessage({
  code,
  message,
  suggestion,
  severity = 'error',
  onRetry,
  onDismiss,
  children,
}: ErrorMessageProps) {
  const styles = severityStyles[severity];
  const icon = severityIcons[severity];

  return (
    <div
      className={`rounded-xl border p-4 ${styles.bg} ${styles.border}`}
      role="alert"
    >
      <div className="flex">
        <div className={`flex-shrink-0 ${styles.icon}`}>{icon}</div>
        <div className="ml-3 flex-1">
          {/* 에러 코드 */}
          {code && (
            <p className={`text-xs font-mono ${styles.text} opacity-60 mb-1`}>
              {code}
            </p>
          )}

          {/* 메인 메시지 */}
          <p className={`text-sm font-medium ${styles.text}`}>{message}</p>

          {/* 제안/도움말 */}
          {suggestion && (
            <p className={`mt-2 text-sm ${styles.text} opacity-80`}>
              {suggestion}
            </p>
          )}

          {/* 추가 컨텐츠 */}
          {children && <div className="mt-3">{children}</div>}

          {/* 액션 버튼들 */}
          {(onRetry || onDismiss) && (
            <div className="mt-4 flex gap-2">
              {onRetry && (
                <button
                  onClick={onRetry}
                  className={`text-sm font-medium ${styles.text} hover:underline focus:outline-none`}
                >
                  다시 시도
                </button>
              )}
              {onDismiss && (
                <button
                  onClick={onDismiss}
                  className={`text-sm ${styles.text} opacity-60 hover:opacity-100 focus:outline-none`}
                >
                  닫기
                </button>
              )}
            </div>
          )}
        </div>

        {/* 닫기 버튼 (X) */}
        {onDismiss && (
          <div className="ml-auto pl-3">
            <button
              onClick={onDismiss}
              className={`inline-flex rounded-md p-1.5 ${styles.text} opacity-40 hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-dark-800 ${
                severity === 'error'
                  ? 'focus:ring-red-500'
                  : severity === 'warning'
                  ? 'focus:ring-amber-500'
                  : 'focus:ring-blue-500'
              }`}
            >
              <span className="sr-only">닫기</span>
              <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                <path
                  fillRule="evenodd"
                  d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                  clipRule="evenodd"
                />
              </svg>
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * 특정 에러 코드에 대한 프리셋 컴포넌트들
 */

export function DangerousQueryError({ onDismiss }: { onDismiss?: () => void }) {
  return (
    <ErrorMessage
      code="DANGEROUS_QUERY"
      message="조회 요청만 가능합니다. 데이터 수정은 지원되지 않습니다."
      severity="warning"
      onDismiss={onDismiss}
    />
  );
}

export function QueryTimeoutError({
  onRetry,
  onDismiss,
}: {
  onRetry?: () => void;
  onDismiss?: () => void;
}) {
  return (
    <ErrorMessage
      code="QUERY_TIMEOUT"
      message="쿼리 실행 시간이 너무 깁니다."
      suggestion="더 구체적인 조건을 추가해보세요. 예: '지난 한 달간', '상위 10개만'"
      severity="warning"
      onRetry={onRetry}
      onDismiss={onDismiss}
    />
  );
}

export function ConnectionError({
  onRetry,
  onDismiss,
}: {
  onRetry?: () => void;
  onDismiss?: () => void;
}) {
  return (
    <ErrorMessage
      code="DATABASE_CONNECTION_ERROR"
      message="현재 데이터를 가져올 수 없습니다."
      suggestion="잠시 후 다시 시도해주세요."
      severity="error"
      onRetry={onRetry}
      onDismiss={onDismiss}
    />
  );
}

export function EmptyResultMessage({
  onDismiss,
}: {
  onDismiss?: () => void;
}) {
  return (
    <ErrorMessage
      code="EMPTY_RESULT"
      message="조건에 맞는 데이터가 없습니다."
      suggestion="다른 조건으로 검색해보시거나, 기간을 넓혀보세요."
      severity="info"
      onDismiss={onDismiss}
    />
  );
}

export default ErrorMessage;
