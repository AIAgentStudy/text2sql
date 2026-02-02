/**
 * 로그인 페이지
 */

import { useNavigate, useLocation } from 'react-router-dom';
import { useEffect } from 'react';
import { LoginForm } from '../components/Auth/LoginForm';
import { useAuth } from '../hooks/useAuth';

export function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { isAuthenticated, isLoading } = useAuth();

  // 이전 페이지 경로 (없으면 홈으로)
  const from = (location.state as { from?: { pathname: string } })?.from?.pathname || '/';

  // 이미 로그인된 경우 리다이렉트
  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      navigate(from, { replace: true });
    }
  }, [isAuthenticated, isLoading, navigate, from]);

  const handleLoginSuccess = () => {
    navigate(from, { replace: true });
  };

  const handleRegisterClick = () => {
    navigate('/register');
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gradient-dark">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-primary-500 border-t-transparent"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-dark flex flex-col justify-center py-12 px-4 sm:px-6 lg:px-8">
      {/* 배경 장식 */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-primary-600/20 rounded-full blur-3xl"></div>
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-primary-700/20 rounded-full blur-3xl"></div>
      </div>

      <div className="relative sm:mx-auto sm:w-full sm:max-w-md">
        <h1 className="text-center text-3xl font-bold text-gradient mb-2">
          Text2SQL Agent
        </h1>
        <h2 className="text-center text-xl text-content-secondary mb-8">로그인</h2>
      </div>

      <div className="relative card py-8 px-4 sm:px-10 max-w-md mx-auto w-full">
        <LoginForm
          onSuccess={handleLoginSuccess}
          onRegisterClick={handleRegisterClick}
        />
      </div>

      <div className="relative mt-4 text-center text-sm text-content-tertiary">
        <p>테스트 계정: admin@logistics.com / admin123</p>
      </div>
    </div>
  );
}
