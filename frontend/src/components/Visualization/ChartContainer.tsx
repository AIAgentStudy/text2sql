/**
 * 차트 컨테이너 컴포넌트
 *
 * 쿼리 결과를 시각화하는 메인 컨테이너입니다.
 * 차트 유형 선택과 자동 추천 기능을 제공합니다.
 */

import { useState, useMemo } from 'react';
import type { QueryResultData } from '../../types';
import { BarChartComponent } from './BarChart';
import { LineChartComponent } from './LineChart';
import { PieChartComponent } from './PieChart';
import { ChartSelector, type ChartType } from './ChartSelector';

interface ChartContainerProps {
  data: QueryResultData;
  onClose: () => void;
}

interface ChartConfig {
  xAxis: string;
  yAxis: string[];
  labelField?: string;
}

export function ChartContainer({ data, onClose }: ChartContainerProps) {
  const { rows, columns } = data;

  // 숫자형 컬럼과 카테고리형 컬럼 분류
  const { numericColumns, categoryColumns } = useMemo(() => {
    const numeric: string[] = [];
    const category: string[] = [];

    columns.forEach((col) => {
      const dataType = col.data_type.toLowerCase();
      if (dataType === 'unknown') {
        const sampleValues = rows.slice(0, 5).map(r => r[col.name]).filter(v => v != null);
        const isNumeric = sampleValues.length > 0 && sampleValues.every(v => typeof v === 'number');
        if (isNumeric) numeric.push(col.name);
        else category.push(col.name);
        return;
      }
      if (
        ['integer', 'bigint', 'smallint', 'decimal', 'numeric', 'real', 'double precision', 'float'].some(
          (t) => dataType.includes(t)
        )
      ) {
        numeric.push(col.name);
      } else {
        category.push(col.name);
      }
    });

    return { numericColumns: numeric, categoryColumns: category };
  }, [columns, rows]);

  // 추천 차트 유형 결정
  const recommendedChartType = useMemo((): ChartType => {
    // 비율 데이터인지 확인 (합이 100에 가까운지)
    if (numericColumns.length >= 1 && rows.length <= 10) {
      const firstNumCol = numericColumns[0];
      const total = rows.reduce((sum, row) => sum + (Number(row[firstNumCol]) || 0), 0);
      if (total >= 90 && total <= 110) {
        return 'pie';
      }
    }

    // 숫자 컬럼 2개 이상이면 LineChart
    if (numericColumns.length >= 2) {
      return 'line';
    }

    // 카테고리 + 숫자면 BarChart
    if (categoryColumns.length >= 1 && numericColumns.length >= 1) {
      return 'bar';
    }

    // 기본값
    return 'bar';
  }, [numericColumns, categoryColumns, rows]);

  const [chartType, setChartType] = useState<ChartType>(recommendedChartType);

  // 차트 설정
  const chartConfig = useMemo((): ChartConfig => {
    const xAxis = categoryColumns[0] || numericColumns[0] || columns[0]?.name || '';
    const yAxis = numericColumns.length > 0 ? numericColumns.slice(0, 3) : [columns[1]?.name || ''];

    return {
      xAxis,
      yAxis,
      labelField: categoryColumns[0],
    };
  }, [numericColumns, categoryColumns, columns]);

  // 차트 데이터 준비
  const chartData = useMemo(() => {
    return rows.map((row) => {
      const item: Record<string, string | number> = {};
      columns.forEach((col) => {
        const value = row[col.name];
        item[col.name] = typeof value === 'number' ? value : String(value ?? '');
      });
      return item;
    });
  }, [rows, columns]);

  // 데이터가 없거나 차트를 그릴 수 없는 경우
  if (rows.length === 0 || columns.length < 2) {
    return (
      <div className="card p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-content-primary">데이터 시각화</h3>
          <button
            onClick={onClose}
            className="text-content-tertiary hover:text-content-primary transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <p className="text-content-secondary text-center py-8">
          시각화할 수 있는 데이터가 충분하지 않습니다.
        </p>
      </div>
    );
  }

  return (
    <div className="card p-6">
      {/* 헤더 */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-content-primary">데이터 시각화</h3>
        <button
          onClick={onClose}
          className="text-content-tertiary hover:text-content-primary transition-colors"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      {/* 차트 유형 선택 */}
      <ChartSelector
        selected={chartType}
        recommended={recommendedChartType}
        onChange={setChartType}
      />

      {/* 차트 영역 */}
      <div className="mt-4 h-80">
        {chartType === 'bar' && (
          <BarChartComponent
            data={chartData}
            xAxisKey={chartConfig.xAxis}
            yAxisKeys={chartConfig.yAxis}
          />
        )}
        {chartType === 'line' && (
          <LineChartComponent
            data={chartData}
            xAxisKey={chartConfig.xAxis}
            yAxisKeys={chartConfig.yAxis}
          />
        )}
        {chartType === 'pie' && (
          <PieChartComponent
            data={chartData}
            dataKey={chartConfig.yAxis[0]}
            nameKey={chartConfig.labelField || chartConfig.xAxis}
          />
        )}
      </div>

      {/* 차트 정보 */}
      <div className="mt-4 text-xs text-content-tertiary">
        <p>X축: {chartConfig.xAxis} | Y축: {chartConfig.yAxis.join(', ')}</p>
        <p>데이터 행 수: {rows.length}개</p>
      </div>
    </div>
  );
}
