/**
 * 파이 차트 컴포넌트
 *
 * Recharts를 사용한 파이 차트입니다.
 */

import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

// 다크 테마용 차트 색상 팔레트 (보라/파랑 계열)
const COLORS = [
  '#a855f7', '#6366f1', '#3b82f6', '#06b6d4', '#10b981',
  '#f59e0b', '#ec4899', '#84cc16', '#f97316', '#8b5cf6',
];

interface PieChartProps {
  data: Record<string, string | number>[];
  dataKey: string;
  nameKey: string;
}

export function PieChartComponent({ data, dataKey, nameKey }: PieChartProps) {
  // 데이터 형식 변환
  const chartData = data.map((item) => ({
    name: String(item[nameKey] ?? ''),
    value: Number(item[dataKey]) || 0,
  }));

  // 커스텀 라벨 렌더러
  const renderCustomizedLabel = ({
    cx,
    cy,
    midAngle,
    innerRadius,
    outerRadius,
    percent,
  }: {
    cx: number;
    cy: number;
    midAngle: number;
    innerRadius: number;
    outerRadius: number;
    percent: number;
  }) => {
    const RADIAN = Math.PI / 180;
    const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
    const x = cx + radius * Math.cos(-midAngle * RADIAN);
    const y = cy + radius * Math.sin(-midAngle * RADIAN);

    if (percent < 0.05) return null; // 5% 미만은 라벨 표시 안함

    return (
      <text
        x={x}
        y={y}
        fill="white"
        textAnchor="middle"
        dominantBaseline="central"
        fontSize={12}
        fontWeight="bold"
      >
        {`${(percent * 100).toFixed(0)}%`}
      </text>
    );
  };

  return (
    <ResponsiveContainer width="100%" height="100%">
      <PieChart>
        <Pie
          data={chartData}
          cx="50%"
          cy="50%"
          labelLine={false}
          label={renderCustomizedLabel}
          outerRadius={120}
          fill="#8884d8"
          dataKey="value"
        >
          {chartData.map((_, index) => (
            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
          ))}
        </Pie>
        <Tooltip
          contentStyle={{
            backgroundColor: 'rgba(26, 26, 46, 0.95)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            borderRadius: '12px',
            boxShadow: '0 8px 32px rgba(0, 0, 0, 0.3)',
            color: '#f8fafc',
          }}
          formatter={(value: number) => [value.toLocaleString(), '']}
        />
        <Legend
          layout="vertical"
          align="right"
          verticalAlign="middle"
          formatter={(value: string) => (
            <span style={{ color: '#94a3b8', fontSize: '12px' }}>{value}</span>
          )}
        />
      </PieChart>
    </ResponsiveContainer>
  );
}
