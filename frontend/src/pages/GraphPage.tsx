/**
 * 그래프 페이지
 *
 * LangGraph 워크플로우를 Mermaid 다이어그램으로 시각화합니다.
 */

import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { useAuth } from '../hooks/useAuth';
import { api } from '../services/api';
import { MermaidDiagram } from '../components/Graph/MermaidDiagram';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { ErrorMessage } from '../components/common/ErrorMessage';

export function GraphPage() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['graph-mermaid'],
    queryFn: () => api.getGraphMermaid(),
  });

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  return (
    <div className="h-screen bg-gradient-dark flex flex-col overflow-hidden">
      {/* 헤더 - ChatPage와 동일한 glass 스타일 */}
      <header className="glass border-b border-surface-border relative flex-shrink-0">
        <div className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-primary-500/50 to-transparent"></div>
        <div className="px-6 py-3 flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-gradient">워크플로우 그래프</h1>
            <p className="text-sm text-content-secondary">
              LangGraph 에이전트 워크플로우 시각화
            </p>
          </div>
          <div className="flex items-center gap-4">
            <div className="text-right">
              <p className="text-sm font-medium text-content-primary">
                {user?.name}
              </p>
              <p className="text-xs text-content-tertiary">
                {user?.roles.join(', ')}
              </p>
            </div>
            <button
              onClick={() => navigate('/')}
              className="px-3 py-1.5 text-sm text-content-secondary hover:text-content-primary hover:bg-surface-hover rounded-lg transition-all duration-200"
            >
              채팅으로 돌아가기
            </button>
            <button
              onClick={() => navigate('/guide')}
              className="px-3 py-1.5 text-sm text-content-secondary hover:text-content-primary hover:bg-surface-hover rounded-lg transition-all duration-200"
            >
              이용가이드
            </button>
            <button
              onClick={handleLogout}
              className="px-3 py-1.5 text-sm text-content-secondary hover:text-content-primary hover:bg-surface-hover rounded-lg transition-all duration-200"
            >
              로그아웃
            </button>
          </div>
        </div>
      </header>

      {/* 메인 콘텐츠 */}
      <main className="flex-1 overflow-y-auto p-8">
        {isLoading && (
          <div className="flex items-center justify-center h-full">
            <LoadingSpinner size="lg" text="워크플로우 그래프를 불러오는 중..." />
          </div>
        )}

        {error && (
          <div className="max-w-md mx-auto">
            <ErrorMessage
              message="워크플로우 그래프를 불러올 수 없습니다."
              suggestion="서버 연결을 확인하고 다시 시도해주세요."
              onRetry={() => refetch()}
            />
          </div>
        )}

        {data && (
          <div className="max-w-5xl mx-auto space-y-8">
            {/* 다이어그램 */}
            <div className="w-full bg-white rounded-2xl shadow-sm border border-gray-200 p-8">
              <MermaidDiagram code={data.mermaid} />
            </div>

            {/* 워크플로우 노드 설명 */}
            <div className="w-full bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
              <h2 className="text-lg font-bold text-gray-900 mb-4">워크플로우 노드 설명</h2>
              <div className="space-y-3">
                {[
                  {
                    num: 1,
                    name: 'schema_retrieval',
                    desc: 'DB 스키마 조회 및 사용자 권한에 따른 테이블 필터링',
                    color: 'bg-purple-100 text-purple-700',
                  },
                  {
                    num: 2,
                    name: 'permission_pre_check',
                    desc: '사용자 질문이 접근 불가한 테이블을 필요로 하는지 사전 검증',
                    color: 'bg-red-100 text-red-700',
                  },
                  {
                    num: 3,
                    name: 'query_generation',
                    desc: '자연어 질문을 SQL 쿼리로 변환 (대화 맥락 지원)',
                    color: 'bg-blue-100 text-blue-700',
                  },
                  {
                    num: 4,
                    name: 'query_validation',
                    desc: '생성된 SQL의 3단계 검증 (키워드/스키마/시맨틱)',
                    color: 'bg-amber-100 text-amber-700',
                  },
                  {
                    num: 5,
                    name: 'user_confirmation',
                    desc: '사용자에게 생성된 쿼리 확인 요청 (Human-in-the-Loop)',
                    color: 'bg-green-100 text-green-700',
                  },
                  {
                    num: 6,
                    name: 'query_execution',
                    desc: '검증된 SQL 쿼리 실행 및 결과 반환',
                    color: 'bg-cyan-100 text-cyan-700',
                  },
                  {
                    num: 7,
                    name: 'response_formatting',
                    desc: '실행 결과를 사용자 친화적 메시지로 변환',
                    color: 'bg-indigo-100 text-indigo-700',
                  },
                ].map((node) => (
                  <div key={node.name} className="flex items-start gap-3">
                    <span className={`flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${node.color}`}>
                      {node.num}
                    </span>
                    <div>
                      <span className="font-mono text-sm font-semibold text-gray-900">{node.name}</span>
                      <p className="text-sm text-gray-600 mt-0.5">{node.desc}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
