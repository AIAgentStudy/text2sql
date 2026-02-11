/**
 * 차트 컨테이너 컴포넌트
 *
 * 쿼리 결과를 시각화하는 메인 컨테이너입니다.
 * 차트 유형 선택과 자동 추천 기능을 제공합니다.
 */

import { useState, useMemo, useRef, useCallback } from 'react';
import type { QueryResultData } from '../../types';
import { BarChartComponent } from './BarChart';
import { LineChartComponent } from './LineChart';
import { PieChartComponent } from './PieChart';
import { ChartSelector, type ChartType } from './ChartSelector';
import { isNumericValue, toNumber } from '../../utils/typeChecks';

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
  const chartWrapperRef = useRef<HTMLDivElement>(null);
  const [copyFeedback, setCopyFeedback] = useState<boolean>(false);

  // 숫자형 컬럼과 카테고리형 컬럼 분류
  const { numericColumns, categoryColumns } = useMemo(() => {
    const numeric: string[] = [];
    const category: string[] = [];

    columns.forEach((col) => {
      const dataType = col.data_type.toLowerCase();
      if (dataType === 'unknown') {
        const sampleValues = rows.slice(0, 5).map(r => r[col.name]).filter(v => v != null);
        const isNumeric = sampleValues.length > 0 && sampleValues.every(v => isNumericValue(v));
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
    const numericSet = new Set(numericColumns);
    return rows.map((row) => {
      const item: Record<string, string | number> = {};
      columns.forEach((col) => {
        const value = row[col.name];
        if (numericSet.has(col.name) && isNumericValue(value)) {
          item[col.name] = toNumber(value);
        } else {
          item[col.name] = typeof value === 'number' ? value : String(value ?? '');
        }
      });
      return item;
    });
  }, [rows, columns, numericColumns]);

  // 차트 이미지를 생성하는 헬퍼 함수
  const generateChartImage = useCallback(async (): Promise<Blob | null> => {
    if (!chartWrapperRef.current) return null;
    
    // Recharts는 SVG를 생성하므로 SVG 요소를 찾음
    const svgElement = chartWrapperRef.current.querySelector('svg');
    if (!svgElement) return null;

    // SVG 데이터를 문자열로 직렬화
    const serializer = new XMLSerializer();
    const svgString = serializer.serializeToString(svgElement);
    
    // 캔버스 생성 및 설정
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    if (!ctx) return null;

    // SVG 크기 정보를 사용하거나 부모 요소 크기 사용
    const width = svgElement.clientWidth || 600;
    const height = svgElement.clientHeight || 300;
    canvas.width = width;
    canvas.height = height;

    // 배경을 흰색으로 채우기 (투명 배경 방지)
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, width, height);

    // SVG를 이미지로 로드
    const img = new Image();
    const svgBlob = new Blob([svgString], { type: 'image/svg+xml;charset=utf-8' });
    const url = URL.createObjectURL(svgBlob);

    return new Promise((resolve, reject) => {
      img.onload = () => {
        ctx.drawImage(img, 0, 0);
        URL.revokeObjectURL(url);
        canvas.toBlob((blob) => {
          resolve(blob);
        }, 'image/png');
      };
      img.onerror = () => {
        URL.revokeObjectURL(url);
        reject(new Error('이미지 생성 실패'));
      };
      img.src = url;
    });
  }, []);

  const handleCopyImage = useCallback(async () => {
    try {
      const blob = await generateChartImage();
      if (!blob) throw new Error('Blob creation failed');
      
      const item = new ClipboardItem({ 'image/png': blob });
      await navigator.clipboard.write([item]);
      
      setCopyFeedback(true);
      setTimeout(() => setCopyFeedback(false), 2000);
    } catch (err) {
      console.error('Failed to copy chart image:', err);
      alert('차트 이미지 복사에 실패했습니다.');
    }
  }, [generateChartImage]);

  const handleDownloadImage = useCallback(async () => {
    try {
      const blob = await generateChartImage();
      if (!blob) throw new Error('Blob creation failed');
      
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.setAttribute('href', url);
      link.setAttribute('download', `chart_${new Date().toISOString().slice(0,19).replace(/[:]/g,'')}.png`);
      link.style.visibility = 'hidden';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Failed to download chart image:', err);
      alert('차트 이미지 다운로드에 실패했습니다.');
    }
  }, [generateChartImage]);

  // 데이터가 없거나 차트를 그릴 수 없는 경우
  if (rows.length === 0 || columns.length < 2) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">데이터 시각화</h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-700 transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <p className="text-gray-500 text-center py-8">
          시각화할 수 있는 데이터가 충분하지 않습니다.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
      {/* 헤더 */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">데이터 시각화</h3>
        <div className="flex items-center gap-2">
          <button
            onClick={handleCopyImage}
            className="flex items-center gap-1.5 px-2 py-1 rounded hover:bg-gray-100 text-gray-600 transition-colors text-xs border border-gray-200"
            title="차트를 클립보드에 복사"
          >
             {copyFeedback ? (
              <>
                <svg className="w-3.5 h-3.5 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                <span className="text-green-600">복사됨</span>
              </>
            ) : (
              <>
                <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3" />
                </svg>
                <span>복사</span>
              </>
            )}
          </button>
          <button
            onClick={handleDownloadImage}
            className="flex items-center gap-1.5 px-2 py-1 rounded hover:bg-gray-100 text-gray-600 transition-colors text-xs border border-gray-200"
            title="PNG로 다운로드"
          >
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
            <span>PNG 저장</span>
          </button>
          <div className="w-px h-4 bg-gray-200 mx-1"></div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-700 transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>

      {/* 차트 유형 선택 */}
      <ChartSelector
        selected={chartType}
        recommended={recommendedChartType}
        onChange={setChartType}
      />

      {/* 차트 영역 */}
      <div className="mt-4 h-80" ref={chartWrapperRef}>
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
      <div className="mt-4 text-xs text-gray-500">
        <p>X축: {chartConfig.xAxis} | Y축: {chartConfig.yAxis.join(', ')}</p>
        <p>데이터 행 수: {rows.length}개</p>
      </div>
    </div>
  );
}
