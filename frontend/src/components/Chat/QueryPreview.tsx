/**
 * 쿼리 미리보기 컴포넌트
 *
 * 생성된 SQL 쿼리를 표시하고 사용자가 실행할 수 있는 UI를 제공합니다.
 * Human-in-the-Loop 패턴을 지원합니다.
 */

interface QueryPreviewProps {
  /** 쿼리 ID */
  queryId: string;
  /** 생성된 SQL 쿼리 */
  query: string;
  /** 쿼리에 대한 한국어 설명 */
  explanation: string;
  /** 실행 버튼 클릭 핸들러 */
  onApprove: (queryId: string) => void;
  /** 취소 버튼 클릭 핸들러 */
  onReject?: (queryId: string) => void;
  /** 로딩 상태 */
  isLoading?: boolean;
}

export function QueryPreview({
  queryId,
  query,
  explanation,
  onApprove,
  onReject,
  isLoading = false,
}: QueryPreviewProps) {
  const handleApprove = () => {
    onApprove(queryId);
  };

  const handleReject = () => {
    onReject?.(queryId);
  };

  return (
    <div className="query-preview card p-4">
      {/* 쿼리 설명 */}
      <div className="mb-4">
        <h3 className="text-lg font-medium text-content-primary">
          생성된 쿼리문
        </h3>
        <p className="mt-1 text-sm text-content-secondary">{explanation}</p>
      </div>

      {/* SQL 쿼리 */}
      <div className="mb-4">
        <span className="text-sm font-medium text-content-secondary">
          SQL 쿼리
        </span>
        <div className="code-block mt-2">
          <pre className="overflow-x-auto text-sm">
            <code className="text-emerald-400">{query}</code>
          </pre>
        </div>
      </div>

      {/* 액션 버튼 */}
      <div className="flex justify-end gap-3">
        {onReject && (
          <button
            onClick={handleReject}
            disabled={isLoading}
            className="btn-ghost text-content-secondary hover:text-red-400 hover:bg-red-500/10"
          >
            취소
          </button>
        )}
        <button
          onClick={handleApprove}
          disabled={isLoading}
          className="btn-primary"
        >
          {isLoading ? (
            <span className="flex items-center">
              <svg
                className="-ml-1 mr-2 h-4 w-4 animate-spin text-white"
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
              실행 중...
            </span>
          ) : (
            "실행"
          )}
        </button>
      </div>
    </div>
  );
}

export default QueryPreview;
