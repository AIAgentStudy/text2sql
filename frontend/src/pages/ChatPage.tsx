/**
 * 채팅 페이지
 *
 * 인증된 사용자만 접근 가능한 메인 채팅 인터페이스입니다.
 * 좌측 채팅 사이드바 + 우측 결과 패널의 2패널 레이아웃을 사용합니다.
 */

import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { ChatContainer } from '../components/Chat/ChatContainer';
import { ResultsPanel } from '../components/Chat/ResultsPanel';
import type { QueryResultData } from '../types';

export function ChatPage() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [selectedResult, setSelectedResult] = useState<QueryResultData | null>(null);
  const [selectedQuery, setSelectedQuery] = useState<string | null>(null);

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const handleSelectResult = useCallback((result: QueryResultData, query: string) => {
    setSelectedResult(result);
    setSelectedQuery(query);
  }, []);

  return (
    <div className="h-screen bg-gradient-dark flex flex-col overflow-hidden">
      {/* 헤더 */}
      <header className="glass border-b border-surface-border relative flex-shrink-0">
        {/* 하단 그라디언트 라인 */}
        <div className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-primary-500/50 to-transparent"></div>
        <div className="px-6 py-3 flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-gradient">Text2SQL Agent</h1>
            <p className="text-sm text-content-secondary">자연어로 데이터베이스 질의하기</p>
          </div>

          <div className="flex items-center gap-4">
            {user?.roles.includes('viewer') && !user?.roles.includes('admin') && !user?.roles.includes('manager') && (
              <span className="text-xs text-amber-400 px-2 py-1 rounded bg-amber-400/10 border border-amber-400/20">
                Viewer 권한
              </span>
            )}
            {/* 사용자 정보 */}
            <div className="text-right">
              <p className="text-sm font-medium text-content-primary">{user?.name}</p>
              <p className="text-xs text-content-tertiary">
                {user?.roles.join(', ')}
              </p>
            </div>

            {/* 로그아웃 버튼 */}
            <button
              onClick={handleLogout}
              className="px-3 py-1.5 text-sm text-content-secondary hover:text-content-primary hover:bg-surface-hover rounded-lg transition-all duration-200"
            >
              로그아웃
            </button>
          </div>
        </div>
      </header>

      {/* 메인 콘텐츠: 2패널 레이아웃 */}
      <main className="flex-1 flex flex-row min-h-0">
        {/* 좌측: 채팅 사이드바 */}
        <div className="w-[45%] flex-shrink-0 border-r border-surface-border flex flex-col">
          <ChatContainer onSelectResult={handleSelectResult} />
        </div>

        {/* 우측: 결과 패널 */}
        <div className="flex-1 flex flex-col min-w-0">
          <ResultsPanel result={selectedResult} query={selectedQuery} />
        </div>
      </main>
    </div>
  );
}
