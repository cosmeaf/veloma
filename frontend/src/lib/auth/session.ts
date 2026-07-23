import 'server-only';

import { cookies } from 'next/headers';

import { authedData, BackendError } from '@/lib/api/backend';
import { ACCESS_COOKIE, REFRESH_COOKIE, SESSION_COOKIE, cookieOptions, secondsUntilExpiry } from '@/lib/auth/cookies';
import type { User } from '@/types';

export type TokenPayload = {
  access: string;
  refresh: string;
  session_id?: string;
};

const ACCESS_FALLBACK_SECONDS = 15 * 60;
const REFRESH_FALLBACK_SECONDS = 7 * 24 * 60 * 60;

/** Writes the token cookies. Only callable from Route Handlers and Server Actions. */
export async function storeTokens(tokens: TokenPayload): Promise<void> {
  const store = await cookies();
  store.set(ACCESS_COOKIE, tokens.access, cookieOptions(secondsUntilExpiry(tokens.access, ACCESS_FALLBACK_SECONDS)));
  store.set(REFRESH_COOKIE, tokens.refresh, cookieOptions(secondsUntilExpiry(tokens.refresh, REFRESH_FALLBACK_SECONDS)));
  if (tokens.session_id) {
    store.set(SESSION_COOKIE, tokens.session_id, cookieOptions(secondsUntilExpiry(tokens.refresh, REFRESH_FALLBACK_SECONDS)));
  }
}

export async function clearTokens(): Promise<void> {
  const store = await cookies();
  for (const name of [ACCESS_COOKIE, REFRESH_COOKIE, SESSION_COOKIE]) {
    store.set(name, '', { ...cookieOptions(0), maxAge: 0 });
  }
}

export async function getRefreshToken(): Promise<string | null> {
  const store = await cookies();
  return store.get(REFRESH_COOKIE)?.value ?? null;
}

/** Current user from /api/auth/me/, or null when there is no usable session. */
export async function getCurrentUser(): Promise<User | null> {
  try {
    const data = await authedData<{ user: User }>('/api/auth/me/');
    return data.user;
  } catch (error) {
    if (error instanceof BackendError && (error.status === 401 || error.status === 403)) {
      return null;
    }
    throw error;
  }
}

export function isStaff(user: User): boolean {
  return user.roles.includes('STAFF') || user.roles.includes('STAFF_MANAGER');
}

export function isManager(user: User): boolean {
  return user.roles.includes('STAFF_MANAGER');
}

export function displayName(user: User): string {
  const full = `${user.first_name} ${user.last_name}`.trim();
  return full || user.email;
}

export function homePathFor(user: User): string {
  return isStaff(user) ? '/staff' : '/dashboard';
}
