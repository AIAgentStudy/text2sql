/**
 * 차트 유형 선택 컴포넌트
 */

export type ChartType = 'bar' | 'line' | 'pie';

interface ChartSelectorProps {
  selected: ChartType;
  recommended: ChartType;
  onChange: (type: ChartType) => void;
}

const chartOptions: { type: ChartType; label: string; icon: JSX.Element }[] = [
  {
    type: 'bar',
    label: '막대',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
      </svg>
    ),
  },
  {
    type: 'line',
    label: '선',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
      </svg>
    ),
  },
  {
    type: 'pie',
    label: '파이',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 3.055A9.001 9.001 0 1020.945 13H11V3.055z" />
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.488 9H15V3.512A9.025 9.025 0 0120.488 9z" />
      </svg>
    ),
  },
];

export function ChartSelector({ selected, recommended, onChange }: ChartSelectorProps) {
  return (
    <div className="flex gap-2">
      {chartOptions.map((option) => (
        <button
          key={option.type}
          onClick={() => onChange(option.type)}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl border transition-all duration-200 ${
            selected === option.type
              ? 'border-primary-500/50 bg-primary-600/20 text-primary-300'
              : 'border-surface-border bg-surface/50 text-content-secondary hover:border-primary-500/30 hover:bg-surface-hover hover:text-content-primary'
          }`}
        >
          {option.icon}
          <span className="text-sm font-medium">{option.label}</span>
          {recommended === option.type && (
            <span className="text-xs bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 px-1.5 py-0.5 rounded-md">
              추천
            </span>
          )}
        </button>
      ))}
    </div>
  );
}
