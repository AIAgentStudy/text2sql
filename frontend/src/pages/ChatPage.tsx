/**
 * 채팅 페이지
 *
 * 인증된 사용자만 접근 가능한 메인 채팅 인터페이스입니다.
 */

import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { ChatContainer } from '../components/Chat/ChatContainer';

export function ChatPage() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  return (
    <div className="min-h-screen bg-gray-100 flex flex-col">
      {/* 헤더 */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-4xl mx-auto px-4 py-3 flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-gray-800">Text2SQL Agent</h1>
            <p className="text-sm text-gray-500">자연어로 데이터베이스 질의하기</p>
          </div>

          <div className="flex items-center gap-4">
            {/* 사용자 정보 */}
            <div className="text-right">
              <p className="text-sm font-medium text-gray-800">{user?.name}</p>
              <p className="text-xs text-gray-500">
                {user?.roles.join(', ')}
              </p>
            </div>

            {/* 로그아웃 버튼 */}
            <button
              onClick={handleLogout}
              className="px-3 py-1.5 text-sm text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-lg transition-colors"
            >
              로그아웃
            </button>
          </div>
        </div>
      </header>

      {/* 메인 콘텐츠 */}
      <main className="flex-1 flex flex-col">
        <div className="max-w-4xl mx-auto w-full flex-1 flex flex-col p-4">
          <ChatContainer />
        </div>
      </main>

      {/* 푸터 */}
      <footer className="bg-white border-t border-gray-200 py-3">
        <div className="max-w-4xl mx-auto px-4 text-center text-sm text-gray-500">
          <p>
            자연어 질문을 입력하면 SQL 쿼리를 생성하고 실행합니다.
          </p>
          {user?.roles.includes('viewer') && !user?.roles.includes('admin') && !user?.roles.includes('manager') && (
            <p className="text-yellow-600 mt-1">
              Viewer 권한: 물류 운영 테이블만 조회 가능합니다.
            </p>
          )}
        </div>
      </footer>
    </div>
  );
}
