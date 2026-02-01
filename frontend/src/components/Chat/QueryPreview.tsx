/**
 * 쿼리 미리보기 컴포넌트
 *
 * 생성된 SQL 쿼리와 설명을 표시하고, 실행/취소 버튼을 제공합니다.
 */

import { useState } from "react";

interface QueryPreviewProps {
  /** SQL 쿼리 */
  query: string;
  /** 쿼리에 대한 한국어 설명 */
  explanation: string;
  /** 쿼리 ID */
  queryId: string;
  /** 세션 ID */
  sessionId: string;
  /** 확인 처리 중 여부 */
  isLoading?: boolean;
  /** 실행 버튼 클릭 핸들러 */
  onExecute: () => void;
  /** 취소 버튼 클릭 핸들러 */
  onCancel: () => void;
}

export function QueryPreview({
  query,
  explanation,
  queryId,
  sessionId,
  isLoading = false,
  onExecute,
  onCancel,
}: QueryPreviewProps) {
  const [isCopied, setIsCopied] = useState(false);

  const handleCopyQuery = async () => {
    try {
      await navigator.clipboard.writeText(query);
      setIsCopied(true);
      setTimeout(() => setIsCopied(false), 2000);
    } catch (err) {
      console.error("클립보드 복사 실패:", err);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-md border border-gray-200 overflow-hidden">
      {/* 헤더 */}
      <div className="bg-gray-50 px-4 py-3 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-medium text-gray-700">
            생성된 쿼리 미리보기
          </h3>
          <span className="text-xs text-gray-500">ID: {queryId.slice(0, 8)}...</span>
        </div>
      </div>

      {/* 쿼리 설명 */}
      <div className="px-4 py-3 bg-blue-50 border-b border-blue-100">
        <p className="text-sm text-blue-800">{explanation}</p>
      </div>

      {/* SQL 쿼리 */}
      <div className="relative">
        <pre className="p-4 bg-gray-900 text-gray-100 text-sm overflow-x-auto">
          <code className="language-sql">{query}</code>
        </pre>

        {/* 복사 버튼 */}
        <button
          type="button"
          onClick={handleCopyQuery}
          className="absolute top-2 right-2 px-2 py-1 text-xs bg-gray-700 hover:bg-gray-600 text-gray-200 rounded transition-colors"
          aria-label="쿼리 복사"
        >
          {isCopied ? "복사됨!" : "복사"}
        </button>
      </div>

      {/* 확인 버튼 */}
      <div className="px-4 py-3 bg-gray-50 border-t border-gray-200">
        <div className="flex items-center justify-end space-x-3">
          <button
            type="button"
            onClick={onCancel}
            disabled={isLoading}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            취소
          </button>
          <button
            type="button"
            onClick={onExecute}
            disabled={isLoading}
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isLoading ? (
              <span className="flex items-center">
                <svg
                  className="animate-spin -ml-1 mr-2 h-4 w-4 text-white"
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
    </div>
  );
}

export default QueryPreview;
