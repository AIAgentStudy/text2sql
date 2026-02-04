/**
 * 선 차트 컴포넌트
 *
 * Recharts를 사용한 선 차트입니다.
 */

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

// 다크 테마용 차트 색상 팔레트 (보라/파랑 계열)
const COLORS = ['#a855f7', '#6366f1', '#3b82f6', '#06b6d4', '#10b981', '#f59e0b'];

interface LineChartProps {
  data: Record<string, string | number>[];
  xAxisKey: string;
  yAxisKeys: string[];
}

export function LineChartComponent({ data, xAxisKey, yAxisKeys }: LineChartProps) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <LineChart
        data={data}
        margin={{ top: 20, right: 30, left: 60, bottom: 80 }}
      >
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(0, 0, 0, 0.1)" />
        <XAxis
          dataKey={xAxisKey}
          tick={{ fontSize: 12, fill: '#374151' }}
          angle={-45}
          textAnchor="end"
          height={60}
          interval={0}
          stroke="rgba(0, 0, 0, 0.15)"
        />
        <YAxis
          tick={{ fontSize: 12, fill: '#374151' }}
          tickFormatter={(value) =>
            typeof value === 'number' ? value.toLocaleString() : value
          }
          stroke="rgba(0, 0, 0, 0.15)"
        />
        <Tooltip
          contentStyle={{
            backgroundColor: '#ffffff',
            border: '1px solid #e5e7eb',
            borderRadius: '12px',
            boxShadow: '0 4px 16px rgba(0, 0, 0, 0.1)',
            color: '#111827',
          }}
          labelStyle={{ color: '#374151' }}
          formatter={(value: number) => [value.toLocaleString(), '']}
        />
        <Legend
          wrapperStyle={{ paddingTop: '10px', color: '#374151' }}
        />
        {yAxisKeys.map((key, index) => (
          <Line
            key={key}
            type="monotone"
            dataKey={key}
            stroke={COLORS[index % COLORS.length]}
            strokeWidth={2}
            dot={{ fill: COLORS[index % COLORS.length], strokeWidth: 2 }}
            activeDot={{ r: 6, fill: COLORS[index % COLORS.length], stroke: '#fff', strokeWidth: 2 }}
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}
