/**
 * 쿼리 미리보기 컴포넌트
 *
 * 생성된 SQL 쿼리를 표시하고 사용자가 실행/취소할 수 있는 UI를 제공합니다.
 * Human-in-the-Loop 패턴을 지원합니다.
 */

import { useState } from 'react';

interface QueryPreviewProps {
  /** 쿼리 ID */
  queryId: string;
  /** 생성된 SQL 쿼리 */
  query: string;
  /** 쿼리에 대한 한국어 설명 */
  explanation: string;
  /** 실행 버튼 클릭 핸들러 */
  onApprove: (queryId: string, modifiedQuery?: string) => void;
  /** 취소 버튼 클릭 핸들러 */
  onReject: (queryId: string) => void;
  /** 로딩 상태 */
  isLoading?: boolean;
  /** 수정 가능 여부 */
  allowEdit?: boolean;
}

export function QueryPreview({
  queryId,
  query,
  explanation,
  onApprove,
  onReject,
  isLoading = false,
  allowEdit = true,
}: QueryPreviewProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [modifiedQuery, setModifiedQuery] = useState(query);

  const handleApprove = () => {
    const queryToSubmit = isEditing && modifiedQuery !== query ? modifiedQuery : undefined;
    onApprove(queryId, queryToSubmit);
  };

  const handleReject = () => {
    onReject(queryId);
  };

  const handleEditToggle = () => {
    if (!allowEdit) return;
    setIsEditing(!isEditing);
    if (!isEditing) {
      setModifiedQuery(query);
    }
  };

  return (
    <div className="query-preview rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
      {/* 쿼리 설명 */}
      <div className="mb-4">
        <h3 className="text-lg font-medium text-gray-900">쿼리 미리보기</h3>
        <p className="mt-1 text-sm text-gray-600">{explanation}</p>
      </div>

      {/* SQL 쿼리 */}
      <div className="mb-4">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-gray-700">SQL 쿼리</span>
          {allowEdit && (
            <button
              onClick={handleEditToggle}
              className="text-sm text-blue-600 hover:text-blue-800"
              disabled={isLoading}
            >
              {isEditing ? '편집 취소' : '쿼리 수정'}
            </button>
          )}
        </div>

        {isEditing ? (
          <textarea
            value={modifiedQuery}
            onChange={(e) => setModifiedQuery(e.target.value)}
            className="mt-2 w-full rounded-md border border-gray-300 bg-gray-50 p-3 font-mono text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            rows={6}
            disabled={isLoading}
          />
        ) : (
          <pre className="mt-2 overflow-x-auto rounded-md bg-gray-900 p-3 text-sm text-green-400">
            <code>{query}</code>
          </pre>
        )}

        {isEditing && modifiedQuery !== query && (
          <p className="mt-1 text-xs text-amber-600">
            * 쿼리가 수정되었습니다. 수정된 쿼리는 다시 검증됩니다.
          </p>
        )}
      </div>

      {/* 액션 버튼 */}
      <div className="flex justify-end gap-3">
        <button
          onClick={handleReject}
          disabled={isLoading}
          className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
        >
          취소
        </button>
        <button
          onClick={handleApprove}
          disabled={isLoading}
          className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
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
            '실행'
          )}
        </button>
      </div>
    </div>
  );
}

export default QueryPreview;
