/**
 * 결과 테이블 컴포넌트
 *
 * SQL 쿼리 결과를 테이블 형태로 표시합니다.
 * 페이지네이션, 컬럼 정렬, 시각화 기능을 지원합니다.
 */

import { useState, useMemo } from 'react';
import type { QueryResultData, ColumnInfo } from '../../types';

interface ResultTableProps {
  /** 쿼리 결과 데이터 */
  data: QueryResultData;
  /** 페이지당 행 수 */
  pageSize?: number;
  /** 최대 표시 컬럼 너비 */
  maxColumnWidth?: number;
}

export function ResultTable({
  data,
  pageSize = 10,
  maxColumnWidth = 300,
}: ResultTableProps) {
  const [currentPage, setCurrentPage] = useState(1);
  const [sortColumn, setSortColumn] = useState<string | null>(null);
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');

  const { rows, columns, total_row_count, returned_row_count, is_truncated, execution_time_ms } = data;

  // 정렬된 행
  const sortedRows = useMemo(() => {
    if (!sortColumn) return rows;

    return [...rows].sort((a, b) => {
      const aVal = a[sortColumn];
      const bVal = b[sortColumn];

      if (aVal === null || aVal === undefined) return sortDirection === 'asc' ? 1 : -1;
      if (bVal === null || bVal === undefined) return sortDirection === 'asc' ? -1 : 1;

      if (typeof aVal === 'number' && typeof bVal === 'number') {
        return sortDirection === 'asc' ? aVal - bVal : bVal - aVal;
      }

      const aStr = String(aVal);
      const bStr = String(bVal);
      return sortDirection === 'asc'
        ? aStr.localeCompare(bStr)
        : bStr.localeCompare(aStr);
    });
  }, [rows, sortColumn, sortDirection]);

  // 페이지네이션
  const totalPages = Math.ceil(sortedRows.length / pageSize);
  const paginatedRows = sortedRows.slice(
    (currentPage - 1) * pageSize,
    currentPage * pageSize
  );

  const handleSort = (columnName: string) => {
    if (sortColumn === columnName) {
      setSortDirection((prev) => (prev === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortColumn(columnName);
      setSortDirection('asc');
    }
    setCurrentPage(1);
  };

  const formatCellValue = (value: unknown): string => {
    if (value === null || value === undefined) {
      return '-';
    }
    if (typeof value === 'object') {
      return JSON.stringify(value);
    }
    if (typeof value === 'boolean') {
      return value ? '예' : '아니오';
    }
    return String(value);
  };

  const getColumnType = (column: ColumnInfo): 'text' | 'number' | 'date' => {
    const dataType = column.data_type.toLowerCase();
    if (['integer', 'bigint', 'smallint', 'decimal', 'numeric', 'real', 'double precision', 'float'].some(t => dataType.includes(t))) {
      return 'number';
    }
    if (['date', 'timestamp', 'time'].some(t => dataType.includes(t))) {
      return 'date';
    }
    return 'text';
  };

  if (rows.length === 0) {
    return (
      <div className="rounded-xl glass p-8 text-center">
        <p className="text-content-secondary">조건에 맞는 데이터가 없습니다.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* 결과 요약 */}
      <div className="flex items-center justify-between text-sm text-content-secondary">
        <span>
          총 {total_row_count.toLocaleString()}개 중 {returned_row_count.toLocaleString()}개 표시
          {is_truncated && <span className="ml-2 text-amber-400">(결과가 잘렸습니다)</span>}
        </span>
        <span className="text-content-tertiary">
          실행 시간: {execution_time_ms.toFixed(0)}ms
        </span>
      </div>

      {/* 테이블 */}
      <div className="overflow-x-auto rounded-xl glass">
        <table className="table-dark min-w-full">
          <thead>
            <tr>
              {columns.map((column) => (
                <th
                  key={column.name}
                  onClick={() => handleSort(column.name)}
                  className="cursor-pointer hover:bg-surface-hover transition-colors"
                  style={{ maxWidth: maxColumnWidth }}
                >
                  <div className="flex items-center gap-1">
                    <span className="truncate">{column.name}</span>
                    {sortColumn === column.name && (
                      <svg
                        className={`h-4 w-4 flex-shrink-0 transition-transform ${
                          sortDirection === 'desc' ? 'rotate-180' : ''
                        }`}
                        fill="currentColor"
                        viewBox="0 0 20 20"
                      >
                        <path
                          fillRule="evenodd"
                          d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z"
                          clipRule="evenodd"
                        />
                      </svg>
                    )}
                  </div>
                  {column.data_type !== 'unknown' && (
                    <span className="text-xs font-normal normal-case text-gray-500">
                      {column.data_type}
                    </span>
                  )}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {paginatedRows.map((row, rowIndex) => (
              <tr key={rowIndex}>
                {columns.map((column) => {
                  const columnType = getColumnType(column);
                  return (
                    <td
                      key={column.name}
                      className={`whitespace-nowrap ${
                        columnType === 'number' ? 'text-right font-mono' : 'text-left'
                      } ${row[column.name] === null ? 'text-content-tertiary italic' : ''}`}
                      style={{ maxWidth: maxColumnWidth }}
                    >
                      <span className="block truncate" title={formatCellValue(row[column.name])}>
                        {formatCellValue(row[column.name])}
                      </span>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* 페이지네이션 */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <span className="text-sm text-content-secondary">
            {currentPage} / {totalPages} 페이지
          </span>
          <div className="flex gap-2">
            <button
              onClick={() => setCurrentPage(1)}
              disabled={currentPage === 1}
              className="btn-secondary px-3 py-1.5 text-sm disabled:opacity-50"
            >
              처음
            </button>
            <button
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              disabled={currentPage === 1}
              className="btn-secondary px-3 py-1.5 text-sm disabled:opacity-50"
            >
              이전
            </button>
            <button
              onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
              className="btn-secondary px-3 py-1.5 text-sm disabled:opacity-50"
            >
              다음
            </button>
            <button
              onClick={() => setCurrentPage(totalPages)}
              disabled={currentPage === totalPages}
              className="btn-secondary px-3 py-1.5 text-sm disabled:opacity-50"
            >
              마지막
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default ResultTable;
