/**
 * 인증 API 서비스
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

export interface User {
  id: number;
  email: string;
  name: string;
  is_active: boolean;
  roles: string[];
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface RegisterRequest {
  email: string;
  password: string;
  name: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface AuthError {
  detail: string;
}

const TOKEN_KEY = 'access_token';
const REFRESH_TOKEN_KEY = 'refresh_token';

/**
 * 토큰 저장
 */
export function saveTokens(tokens: TokenResponse): void {
  localStorage.setItem(TOKEN_KEY, tokens.access_token);
  localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh_token);
}

/**
 * 토큰 삭제
 */
export function clearTokens(): void {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
}

/**
 * Access Token 가져오기
 */
export function getAccessToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

/**
 * Refresh Token 가져오기
 */
export function getRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

/**
 * 인증 헤더 생성
 */
export function getAuthHeader(): HeadersInit {
  const token = getAccessToken();
  if (token) {
    return { Authorization: `Bearer ${token}` };
  }
  return {};
}

/**
 * 회원가입
 */
export async function register(data: RegisterRequest): Promise<User> {
  const response = await fetch(`${API_BASE_URL}/api/auth/register`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error: AuthError = await response.json();
    throw new Error(error.detail || '회원가입에 실패했습니다.');
  }

  return response.json();
}

/**
 * 로그인
 */
export async function login(data: LoginRequest): Promise<TokenResponse> {
  const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
    credentials: 'include', // 쿠키 포함
  });

  if (!response.ok) {
    const error: AuthError = await response.json();
    throw new Error(error.detail || '로그인에 실패했습니다.');
  }

  const tokens: TokenResponse = await response.json();
  saveTokens(tokens);
  return tokens;
}

/**
 * 로그아웃
 */
export async function logout(): Promise<void> {
  const token = getAccessToken();

  if (token) {
    try {
      await fetch(`${API_BASE_URL}/api/auth/logout`, {
        method: 'POST',
        headers: {
          ...getAuthHeader(),
        },
        credentials: 'include',
      });
    } catch {
      // 로그아웃 API 실패해도 로컬 토큰은 삭제
    }
  }

  clearTokens();
}

/**
 * 토큰 갱신
 */
export async function refreshToken(): Promise<TokenResponse | null> {
  const refresh = getRefreshToken();

  if (!refresh) {
    return null;
  }

  try {
    const response = await fetch(`${API_BASE_URL}/api/auth/refresh`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ refresh_token: refresh }),
      credentials: 'include',
    });

    if (!response.ok) {
      clearTokens();
      return null;
    }

    const tokens: TokenResponse = await response.json();
    saveTokens(tokens);
    return tokens;
  } catch {
    clearTokens();
    return null;
  }
}

/**
 * 현재 사용자 정보 조회
 */
export async function getCurrentUser(): Promise<User | null> {
  const token = getAccessToken();

  if (!token) {
    return null;
  }

  try {
    const response = await fetch(`${API_BASE_URL}/api/auth/me`, {
      headers: {
        ...getAuthHeader(),
      },
    });

    if (!response.ok) {
      if (response.status === 401) {
        // 토큰 만료 시 갱신 시도
        const newTokens = await refreshToken();
        if (newTokens) {
          return getCurrentUser();
        }
        return null;
      }
      return null;
    }

    return response.json();
  } catch {
    return null;
  }
}

/**
 * 인증 상태 확인
 */
export function isAuthenticated(): boolean {
  return !!getAccessToken();
}
