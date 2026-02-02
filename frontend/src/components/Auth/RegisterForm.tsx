/**
 * 회원가입 폼 컴포넌트
 */

import { useState, type FormEvent } from 'react';
import { useAuth } from '../../hooks/useAuth';

interface RegisterFormProps {
  onSuccess?: () => void;
  onLoginClick?: () => void;
}

export function RegisterForm({ onSuccess, onLoginClick }: RegisterFormProps) {
  const { register } = useAuth();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [role, setRole] = useState<'viewer' | 'manager'>('viewer');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);

    // 비밀번호 확인
    if (password !== confirmPassword) {
      setError('비밀번호가 일치하지 않습니다.');
      return;
    }

    // 비밀번호 길이 확인
    if (password.length < 8) {
      setError('비밀번호는 8자 이상이어야 합니다.');
      return;
    }

    setIsLoading(true);

    try {
      await register({ email, password, name, role });
      onSuccess?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : '회원가입에 실패했습니다.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="w-full max-w-md mx-auto">
      <form onSubmit={handleSubmit} className="space-y-5">
        <div>
          <label
            htmlFor="name"
            className="block text-sm font-medium text-content-secondary mb-2"
          >
            이름
          </label>
          <input
            id="name"
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
            autoComplete="name"
            className="input-dark w-full"
            placeholder="홍길동"
          />
        </div>

        <div>
          <label
            htmlFor="email"
            className="block text-sm font-medium text-content-secondary mb-2"
          >
            이메일
          </label>
          <input
            id="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            autoComplete="email"
            className="input-dark w-full"
            placeholder="email@example.com"
          />
        </div>

        <div>
          <label
            htmlFor="password"
            className="block text-sm font-medium text-content-secondary mb-2"
          >
            비밀번호
          </label>
          <input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            autoComplete="new-password"
            className="input-dark w-full"
            placeholder="8자 이상"
          />
        </div>

        <div>
          <label
            htmlFor="confirmPassword"
            className="block text-sm font-medium text-content-secondary mb-2"
          >
            비밀번호 확인
          </label>
          <input
            id="confirmPassword"
            type="password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            required
            autoComplete="new-password"
            className="input-dark w-full"
            placeholder="비밀번호 재입력"
          />
        </div>

        <div>
          <label
            htmlFor="role"
            className="block text-sm font-medium text-content-secondary mb-2"
          >
            역할 선택
          </label>
          <select
            id="role"
            value={role}
            onChange={(e) => setRole(e.target.value as 'viewer' | 'manager')}
            className="select-dark w-full"
          >
            <option value="viewer">조회자 (Viewer) - 읽기 전용</option>
            <option value="manager">매니저 (Manager) - 읽기/쓰기</option>
          </select>
          <p className="mt-2 text-xs text-content-tertiary">
            역할에 따라 시스템 접근 권한이 달라집니다.
          </p>
        </div>

        {error && (
          <div className="text-red-400 text-sm bg-red-500/10 border border-red-500/20 p-3 rounded-xl">
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={isLoading}
          className="btn-primary w-full"
        >
          {isLoading ? '회원가입 중...' : '회원가입'}
        </button>
      </form>

      <div className="mt-6 text-center text-sm text-content-secondary">
        이미 계정이 있으신가요?{' '}
        <button
          type="button"
          onClick={onLoginClick}
          className="text-primary-400 hover:text-primary-300 font-medium transition-colors"
        >
          로그인
        </button>
      </div>
    </div>
  );
}
