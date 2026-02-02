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
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-blue-500 border-t-transparent"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <h1 className="text-center text-3xl font-bold text-gray-900 mb-2">
          Text2SQL Agent
        </h1>
        <h2 className="text-center text-xl text-gray-600 mb-8">회원가입</h2>
      </div>

      <div className="bg-white py-8 px-4 shadow-lg sm:rounded-lg sm:px-10 max-w-md mx-auto w-full">
        {registered ? (
          <div className="text-center">
            <div className="text-green-500 text-5xl mb-4">✓</div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              회원가입 완료!
            </h3>
            <p className="text-gray-600 mb-4">
              가입이 완료되었습니다. 로그인해주세요.
            </p>
            <button
              onClick={handleLoginClick}
              className="w-full py-2 px-4 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors"
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
