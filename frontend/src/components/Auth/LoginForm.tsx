/**
 * 로그인 폼 컴포넌트
 */

import { useState, type FormEvent } from "react";
import { useAuth } from "../../hooks/useAuth";

interface LoginFormProps {
  onSuccess?: () => void;
  onRegisterClick?: () => void;
}

export function LoginForm({ onSuccess, onRegisterClick }: LoginFormProps) {
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      await login({ email, password });
      onSuccess?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : "로그인에 실패했습니다.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="w-full max-w-md mx-auto">
      <form onSubmit={handleSubmit} className="space-y-5">
        <div>
          <label
            htmlFor="email"
            className="block text-sm font-medium text-white mb-2"
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
            className="block text-sm font-medium text-white mb-2"
          >
            비밀번호
          </label>
          <input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            autoComplete="current-password"
            className="input-dark w-full"
            placeholder="********"
          />
        </div>

        {error && (
          <div className="text-red-700 text-sm bg-red-300/70 border border-red-500/20 p-3 rounded-xl">
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={isLoading}
          className="btn-primary w-full"
        >
          {isLoading ? "로그인 중..." : "로그인"}
        </button>
      </form>

      <div className="mt-6 text-center font-semibold text-sm text-gray-300">
        계정이 없으신가요?{" "}
        <button
          type="button"
          onClick={onRegisterClick}
          className="text-blue-400 hover:text-blue-800 font-semibold transition-colors"
        >
          회원가입
        </button>
      </div>

      {/* 테스트 계정 안내 */}
      <div className="mt-6 p-4 bg-surface-secondary/50 rounded-xl border border-surface-border bg-gray-100">
        <p className="text-xs text-black mb-3 text-center font-medium">
          테스트 계정
        </p>
        <div className="space-y-2 text-xs">
          <div className="flex justify-between items-center text-black">
            <span className="text-amber-400 font-semibold">Admin</span>
            <span className="font-mono">admin@test.com / admin123</span>
          </div>
          <div className="flex justify-between items-center text-black">
            <span className="text-blue-400 font-semibold">Manager</span>
            <span className="font-mono">manager@test.com / admin123</span>
          </div>
          <div className="flex justify-between items-center text-black">
            <span className="text-green-400 font-semibold">Viewer</span>
            <span className="font-mono">viewer@test.com / admin123</span>
          </div>
        </div>
        <p className="text-xs text-gray-500 mt-3 text-center">
          역할별로 조회 가능한 테이블이 다릅니다
        </p>
      </div>
    </div>
  );
}
