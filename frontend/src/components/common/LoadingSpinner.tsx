/**
 * 로딩 스피너 컴포넌트
 *
 * 다양한 크기와 스타일의 로딩 인디케이터를 제공합니다.
 */

interface LoadingSpinnerProps {
  /** 스피너 크기 */
  size?: 'sm' | 'md' | 'lg';
  /** 색상 */
  color?: 'primary' | 'white' | 'gray';
  /** 로딩 텍스트 */
  text?: string;
  /** 전체 화면 오버레이 */
  fullScreen?: boolean;
}

const sizeClasses = {
  sm: 'h-4 w-4',
  md: 'h-6 w-6',
  lg: 'h-10 w-10',
};

const colorClasses = {
  primary: 'text-blue-600',
  white: 'text-white',
  gray: 'text-gray-400',
};

export function LoadingSpinner({
  size = 'md',
  color = 'primary',
  text,
  fullScreen = false,
}: LoadingSpinnerProps) {
  const spinner = (
    <div className="flex flex-col items-center justify-center gap-2">
      <svg
        className={`animate-spin ${sizeClasses[size]} ${colorClasses[color]}`}
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
        aria-hidden="true"
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
      {text && (
        <span className={`text-sm ${colorClasses[color]}`}>{text}</span>
      )}
    </div>
  );

  if (fullScreen) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-white/80 backdrop-blur-sm">
        {spinner}
      </div>
    );
  }

  return spinner;
}

/**
 * 인라인 로딩 스피너 (텍스트와 함께)
 */
export function InlineSpinner({ text = '처리 중...' }: { text?: string }) {
  return (
    <span className="inline-flex items-center gap-2 text-sm text-gray-500">
      <LoadingSpinner size="sm" color="gray" />
      {text}
    </span>
  );
}

/**
 * 상태별 로딩 메시지
 */
export function StatusSpinner({
  status,
}: {
  status: 'generating' | 'validating' | 'executing' | 'pending';
}) {
  const messages: Record<string, string> = {
    pending: '요청을 처리하는 중입니다...',
    generating: 'SQL 쿼리를 생성하는 중입니다...',
    validating: '쿼리를 검증하는 중입니다...',
    executing: '쿼리를 실행하는 중입니다...',
  };

  return (
    <div className="flex items-center gap-3 rounded-lg bg-blue-50 p-4 text-blue-700">
      <LoadingSpinner size="sm" color="primary" />
      <span className="text-sm">{messages[status]}</span>
    </div>
  );
}

export default LoadingSpinner;
