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
      <main className="flex-1 overflow-y-auto flex items-center justify-center p-8">
        {isLoading && (
          <LoadingSpinner size="lg" text="워크플로우 그래프를 불러오는 중..." />
        )}

        {error && (
          <div className="max-w-md w-full">
            <ErrorMessage
              message="워크플로우 그래프를 불러올 수 없습니다."
              suggestion="서버 연결을 확인하고 다시 시도해주세요."
              onRetry={() => refetch()}
            />
          </div>
        )}

        {data && (
          <div className="w-full max-w-5xl bg-white rounded-2xl shadow-sm border border-gray-200 p-8">
            <MermaidDiagram code={data.mermaid} />
          </div>
        )}
      </main>
    </div>
  );
}
