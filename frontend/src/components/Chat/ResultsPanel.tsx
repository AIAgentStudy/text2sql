/**
 * 결과 패널 컴포넌트
 *
 * 쿼리 결과를 테이블과 차트로 표시하는 우측 메인 패널입니다.
 */

import { useState, useMemo } from 'react';
import type { QueryResultData } from '../../types';
import { ResultTable } from './ResultTable';
import { ChartContainer } from '../Visualization/ChartContainer';
import { isNumericValue } from '../../utils/typeChecks';

type TabType = 'table' | 'chart';

interface ResultsPanelProps {
  result: QueryResultData | null;
  query: string | null;
}

export function ResultsPanel({ result, query }: ResultsPanelProps) {
  const [activeTab, setActiveTab] = useState<TabType>('table');

  const canVisualize = useMemo(() => {
    if (!result) return false;
    const { rows, columns } = result;
    if (rows.length === 0 || columns.length < 2) return false;

    // 숫자형 컬럼이 1개 이상 있어야 시각화 가능
    const hasNumericColumn = columns.some((col) => {
      const dataType = col.data_type.toLowerCase();
      if (dataType === 'unknown') {
        const sampleValues = rows.slice(0, 5).map(r => r[col.name]).filter(v => v != null);
        return sampleValues.length > 0 && sampleValues.every(v => isNumericValue(v));
      }
      return ['integer', 'bigint', 'smallint', 'decimal', 'numeric', 'real', 'double precision', 'float'].some(
        (t) => dataType.includes(t)
      );
    });

    return hasNumericColumn;
  }, [result]);

  if (!result) {
    return (
      <div className="flex h-full flex-col items-center justify-center text-center px-8">
        <div className="relative mb-6">
          <div className="absolute inset-0 bg-gradient-to-r from-primary-600/10 to-accent-500/10 rounded-full blur-2xl scale-150"></div>
          <div className="relative rounded-2xl bg-dark-700/50 border border-surface-border p-5">
            <svg
              className="h-10 w-10 text-content-tertiary"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M3 10h18M3 14h18m-9-4v8m-7 0h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"
              />
            </svg>
          </div>
        </div>
        <h3 className="text-lg font-semibold text-content-secondary">결과 패널</h3>
        <p className="mt-2 max-w-sm text-sm text-content-tertiary">
          쿼리를 실행하면 이곳에 결과가 표시됩니다.
        </p>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col overflow-hidden">
      {/* 헤더: 실행된 쿼리 */}
      {query && (
        <div className="border-b border-surface-border px-4 py-3 bg-dark-800/50 flex-shrink-0">
          <div className="code-block">
            <pre className="overflow-x-auto text-xs">
              <code className="text-emerald-400">{query}</code>
            </pre>
          </div>
        </div>
      )}

      {/* 탭 바 (시각화 가능한 경우에만 표시) */}
      {canVisualize && (
        <div className="flex border-b border-surface-border px-4 bg-dark-700/50 flex-shrink-0">
          <button
            onClick={() => setActiveTab('table')}
            className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-all duration-200 ${
              activeTab === 'table'
                ? 'border-primary-500 text-primary-400 bg-primary-500/10'
                : 'border-transparent text-content-tertiary hover:text-content-secondary hover:bg-dark-600/30'
            }`}
          >
            <span className="flex items-center gap-2">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M3 10h18M3 14h18m-9-4v8m-7 0h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"
                />
              </svg>
              테이블
            </span>
          </button>
          <button
            onClick={() => setActiveTab('chart')}
            className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-all duration-200 ${
              activeTab === 'chart'
                ? 'border-primary-500 text-primary-400 bg-primary-500/10'
                : 'border-transparent text-content-tertiary hover:text-content-secondary hover:bg-dark-600/30'
            }`}
          >
            <span className="flex items-center gap-2">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                />
              </svg>
              시각화
            </span>
          </button>
        </div>
      )}

      {/* 컨텐츠 */}
      <div className={`flex-1 overflow-auto p-4 ${activeTab === 'chart' && canVisualize ? 'bg-white' : ''}`}>
        {activeTab === 'chart' && canVisualize ? (
          <ChartContainer data={result} onClose={() => setActiveTab('table')} />
        ) : (
          <ResultTable data={result} />
        )}
      </div>
    </div>
  );
}
