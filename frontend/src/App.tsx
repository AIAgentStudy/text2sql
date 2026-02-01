/**
 * Text2SQL Agent 메인 앱 컴포넌트
 *
 * React Query 프로바이더와 메인 레이아웃을 포함합니다.
 */

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ChatContainer } from './components/Chat/ChatContainer';

// React Query 클라이언트 설정
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60, // 1분
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <div className="flex h-screen flex-col bg-slate-50">
        {/* 헤더 */}
        <header className="flex-shrink-0 border-b bg-white shadow-sm">
          <div className="mx-auto max-w-4xl px-4 py-4">
            <h1 className="text-xl font-semibold text-slate-800">
              Text2SQL Agent
            </h1>
            <p className="text-sm text-slate-500">
              자연어로 데이터베이스를 조회하세요
            </p>
          </div>
        </header>

        {/* 메인 컨텐츠 */}
        <main className="min-h-0 flex-1">
          <div className="mx-auto h-full max-w-4xl px-4 py-4">
            <div className="flex h-full flex-col rounded-lg border bg-white shadow-sm">
              <ChatContainer />
            </div>
          </div>
        </main>

        {/* 푸터 */}
        <footer className="flex-shrink-0 border-t bg-white py-2">
          <div className="mx-auto max-w-4xl px-4">
            <p className="text-center text-xs text-gray-400">
              Text2SQL Agent v0.1.0 | 데이터 조회 전용
            </p>
          </div>
        </footer>
      </div>
    </QueryClientProvider>
  );
}

export default App;
