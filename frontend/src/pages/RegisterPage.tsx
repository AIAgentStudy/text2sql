/**
 * 회원가입 페이지
 */

import { useNavigate } from 'react-router-dom';
import { useEffect, useState } from 'react';
import { RegisterForm } from '../components/Auth/RegisterForm';
import { useAuth } from '../hooks/useAuth';

export function RegisterPage() {
  const navigate = useNavigate();
  const { isAuthenticated, isLoading } = useAuth();
  const [registered, setRegistered] = useState(false);

  // 이미 로그인된 경우 리다이렉트
  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      navigate('/', { replace: true });
    }
  }, [isAuthenticated, isLoading, navigate]);

  const handleRegisterSuccess = () => {
    setRegistered(true);
  };

  const handleLoginClick = () => {
    navigate('/login');
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
        <h2 className="text-center text-xl text-content-secondary mb-8">회원가입</h2>
      </div>

      <div className="relative card py-8 px-4 sm:px-10 max-w-md mx-auto w-full">
        {registered ? (
          <div className="text-center">
            <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-gradient-to-r from-emerald-500 to-emerald-600 flex items-center justify-center">
              <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h3 className="text-xl font-semibold text-content-primary mb-2">
              회원가입 완료!
            </h3>
            <p className="text-content-secondary mb-6">
              가입이 완료되었습니다. 로그인해주세요.
            </p>
            <button
              onClick={handleLoginClick}
              className="btn-primary w-full"
            >
              로그인하기
            </button>
          </div>
        ) : (
          <RegisterForm
            onSuccess={handleRegisterSuccess}
            onLoginClick={handleLoginClick}
          />
        )}
      </div>
    </div>
  );
}
