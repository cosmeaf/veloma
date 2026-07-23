import 'server-only';

import { cookies, headers } from 'next/headers';
import { redirect } from 'next/navigation';

import { ACCESS_COOKIE, REFRESH_COOKIE } from '@/lib/auth/cookies';
import type { ApiResponse } from '@/types';

export const BACKEND_URL = (process.env.BACKEND_URL ?? 'http://localhost:19080').replace(/\/$/, '');

export class BackendError extends Error {
  status: number;
  errors?: Record<string, unknown>;

  constructor(message: string, status: number, errors?: Record<string, unknown>) {
    super(message);
    this.name = 'BackendError';
    this.status = status;
    this.errors = errors;
  }
}

type FetchOptions = RequestInit & { accessToken?: string | null };

/** Raw call to Django. No cookies are attached unless a token is passed in. */
export async function backendFetch<T>(path: string, options: FetchOptions = {}): Promise<ApiResponse<T>> {
  const { accessToken, headers, ...rest } = options;
  const requestHeaders = new Headers(headers);
  if (!requestHeaders.has('Content-Type') && !(rest.body instanceof FormData)) {
    requestHeaders.set('Content-Type', 'application/json');
  }
  if (accessToken) {
    requestHeaders.set('Authorization', `Bearer ${accessToken}`);
  }

  const response = await fetch(`${BACKEND_URL}${path}`, {
    ...rest,
    headers: requestHeaders,
    cache: 'no-store',
  });

  const text = await response.text();
  let payload: ApiResponse<T>;
  try {
    payload = text ? (JSON.parse(text) as ApiResponse<T>) : { success: response.ok, message: '' };
  } catch {
    payload = { success: false, message: text.slice(0, 200) };
  }

  if (!response.ok) {
    throw new BackendError(
      readableError(payload),
      response.status,
      payload.errors as Record<string, unknown> | undefined,
    );
  }
  return payload;
}

/**
 * Forwards the real client IP and user agent to Django.
 *
 * Without this every server-rendered call would reach the API from the single
 * frontend container address: the per-IP rate limit would treat the whole
 * application as one client, and the audit trail would record the BFF instead
 * of the person. Django only honours these headers from trusted proxies.
 */
async function forwardedHeaders(): Promise<Headers> {
  const incoming = await headers();
  const forwarded = new Headers();
  const clientIp = incoming.get('x-forwarded-for') ?? incoming.get('x-real-ip');
  if (clientIp) forwarded.set('X-Forwarded-For', clientIp);
  const agent = incoming.get('user-agent');
  if (agent) forwarded.set('User-Agent', agent);
  return forwarded;
}

/**
 * Server-side call using the access token stored in the HttpOnly cookie.
 *
 * An expired or revoked session sends the visitor back to the sign-in page
 * instead of surfacing a server error.
 */
export async function authedFetch<T>(path: string, options: RequestInit = {}): Promise<ApiResponse<T>> {
  const store = await cookies();
  const accessToken = store.get(ACCESS_COOKIE)?.value ?? null;
  if (!accessToken) {
    redirect('/entrar');
  }

  const forwarded = await forwardedHeaders();
  for (const [key, value] of new Headers(options.headers ?? {})) {
    forwarded.set(key, value);
  }

  try {
    return await backendFetch<T>(path, { ...options, headers: forwarded, accessToken });
  } catch (error) {
    if (error instanceof BackendError && error.status === 401) {
      redirect('/entrar');
    }
    throw error;
  }
}

/** Convenience wrapper that returns `data` and throws on failure. */
export async function authedData<T>(path: string, options: RequestInit = {}): Promise<T> {
  const payload = await authedFetch<T>(path, options);
  return payload.data as T;
}

export async function hasSession(): Promise<boolean> {
  const store = await cookies();
  return Boolean(store.get(ACCESS_COOKIE)?.value ?? store.get(REFRESH_COOKIE)?.value);
}

/** Flattens the backend error envelope into a single readable sentence. */
export function readableError(payload: ApiResponse<unknown>): string {
  const errors = payload.errors;
  if (errors && typeof errors === 'object') {
    const parts: string[] = [];
    for (const value of Object.values(errors)) {
      if (Array.isArray(value)) parts.push(...value.map(String));
      else if (typeof value === 'string') parts.push(value);
    }
    if (parts.length) return parts.join(' ');
  }
  return payload.message || 'Ocorreu um erro inesperado.';
}
