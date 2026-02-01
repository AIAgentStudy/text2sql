/**
 * 확인 버튼 컴포넌트
 *
 * 쿼리 실행 확인을 위한 실행/취소 버튼을 제공합니다.
 */

interface ConfirmButtonsProps {
  /** 실행 버튼 클릭 핸들러 */
  onExecute: () => void;
  /** 취소 버튼 클릭 핸들러 */
  onCancel: () => void;
  /** 로딩 상태 */
  isLoading?: boolean;
  /** 비활성화 상태 */
  disabled?: boolean;
  /** 버튼 크기 */
  size?: "sm" | "md" | "lg";
  /** 실행 버튼 텍스트 */
  executeText?: string;
  /** 취소 버튼 텍스트 */
  cancelText?: string;
}

const sizeClasses = {
  sm: "px-3 py-1.5 text-xs",
  md: "px-4 py-2 text-sm",
  lg: "px-6 py-3 text-base",
};

export function ConfirmButtons({
  onExecute,
  onCancel,
  isLoading = false,
  disabled = false,
  size = "md",
  executeText = "실행",
  cancelText = "취소",
}: ConfirmButtonsProps) {
  const isDisabled = isLoading || disabled;
  const buttonSize = sizeClasses[size];

  return (
    <div className="flex items-center justify-end space-x-3">
      {/* 취소 버튼 */}
      <button
        type="button"
        onClick={onCancel}
        disabled={isDisabled}
        className={`
          ${buttonSize}
          font-medium
          text-gray-700
          bg-white
          border border-gray-300
          rounded-md
          hover:bg-gray-50
          focus:outline-none
          focus:ring-2
          focus:ring-offset-2
          focus:ring-gray-500
          disabled:opacity-50
          disabled:cursor-not-allowed
          transition-colors
        `}
        aria-label={cancelText}
      >
        {cancelText}
      </button>

      {/* 실행 버튼 */}
      <button
        type="button"
        onClick={onExecute}
        disabled={isDisabled}
        className={`
          ${buttonSize}
          font-medium
          text-white
          bg-blue-600
          border border-transparent
          rounded-md
          hover:bg-blue-700
          focus:outline-none
          focus:ring-2
          focus:ring-offset-2
          focus:ring-blue-500
          disabled:opacity-50
          disabled:cursor-not-allowed
          transition-colors
        `}
        aria-label={executeText}
      >
        {isLoading ? (
          <span className="flex items-center">
            <LoadingSpinner className="mr-2" />
            실행 중...
          </span>
        ) : (
          executeText
        )}
      </button>
    </div>
  );
}

/**
 * 로딩 스피너 컴포넌트
 */
interface LoadingSpinnerProps {
  className?: string;
  size?: number;
}

function LoadingSpinner({ className = "", size = 16 }: LoadingSpinnerProps) {
  return (
    <svg
      className={`animate-spin ${className}`}
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
      width={size}
      height={size}
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
  );
}

export default ConfirmButtons;
