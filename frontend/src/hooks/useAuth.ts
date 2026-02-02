/**
 * 인증 훅
 */

import { useContext } from 'react';
import { AuthContext } from '../contexts/AuthContext';

export function useAuth() {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }

  return context;
}

/**
 * 특정 역할 확인 훅
 */
export function useHasRole(role: string): boolean {
  const { user } = useAuth();
  return user?.roles.includes(role) ?? false;
}

/**
 * Admin 역할 확인 훅
 */
export function useIsAdmin(): boolean {
  return useHasRole('admin');
}

/**
 * Manager 이상 역할 확인 훅
 */
export function useIsManagerOrAbove(): boolean {
  const { user } = useAuth();
  return user?.roles.some((role) => ['admin', 'manager'].includes(role)) ?? false;
}
