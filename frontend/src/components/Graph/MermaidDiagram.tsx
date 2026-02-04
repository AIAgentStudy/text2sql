/**
 * Mermaid 다이어그램 렌더링 컴포넌트
 *
 * LangGraph 워크플로우를 Mermaid 구문으로 시각화합니다.
 */

import { useEffect, useRef, useState } from 'react';
import mermaid from 'mermaid';

interface MermaidDiagramProps {
  code: string;
}

mermaid.initialize({
  startOnLoad: false,
  theme: 'default',
  securityLevel: 'loose',
  flowchart: {
    useMaxWidth: false,
    htmlLabels: true,
    curve: 'basis',
  },
});

export function MermaidDiagram({ code }: MermaidDiagramProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!containerRef.current || !code) return;

    const renderDiagram = async () => {
      try {
        setError(null);
        const id = `mermaid-${Date.now()}`;
        const { svg } = await mermaid.render(id, code);
        if (containerRef.current) {
          containerRef.current.innerHTML = svg;
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : '다이어그램 렌더링에 실패했습니다.');
      }
    };

    renderDiagram();
  }, [code]);

  if (error) {
    return (
      <div className="rounded-xl border border-red-500/20 bg-red-500/10 p-4 text-sm text-red-300">
        다이어그램 렌더링 오류: {error}
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      className="w-full overflow-auto [&>svg]:mx-auto [&>svg]:block"
    />
  );
}
