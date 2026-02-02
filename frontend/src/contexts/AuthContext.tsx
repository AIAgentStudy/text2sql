/**
 * 인증 상태 관리 Context
 */

import {
  createContext,
  useCallback,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';
import {
  clearTokens,
  getCurrentUser,
  login as loginApi,
  logout as logoutApi,
  register as registerApi,
  type LoginRequest,
  type RegisterRequest,
  type User,
} from '../services/auth';

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (data: LoginRequest) => Promise<void>;
  register: (data: RegisterRequest) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

export const AuthContext = createContext<AuthContextType | null>(null);

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const isAuthenticated = useMemo(() => user !== null, [user]);

  /**
   * 사용자 정보 새로고침
   */
  const refreshUser = useCallback(async () => {
    try {
      const currentUser = await getCurrentUser();
      setUser(currentUser);
    } catch {
      setUser(null);
      clearTokens();
    }
  }, []);

  /**
   * 초기 인증 상태 확인
   */
  useEffect(() => {
    const initAuth = async () => {
      setIsLoading(true);
      await refreshUser();
      setIsLoading(false);
    };
    initAuth();
  }, [refreshUser]);

  /**
   * 로그인
   */
  const login = useCallback(async (data: LoginRequest) => {
    await loginApi(data);
    await refreshUser();
  }, [refreshUser]);

  /**
   * 회원가입
   */
  const register = useCallback(async (data: RegisterRequest) => {
    await registerApi(data);
  }, []);

  /**
   * 로그아웃
   */
  const logout = useCallback(async () => {
    await logoutApi();
    setUser(null);
  }, []);

  const value = useMemo(
    () => ({
      user,
      isLoading,
      isAuthenticated,
      login,
      register,
      logout,
      refreshUser,
    }),
    [user, isLoading, isAuthenticated, login, register, logout, refreshUser]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
