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

/**
 * Real client IP and user agent, forwarded to Django on every call.
 *
 * Without this the API would see the single frontend container: the audit
 * trail would record `10.x.x.x` and an empty user agent (parsed as
 * "Other · Other · Other"), and the per-IP rate limit would treat the whole
 * app as one client. Django only honours these headers from trusted proxies.
 * Prefers Cloudflare's real-client header, then the proxy chain.
 */
export async function clientForwardHeaders(): Promise<Headers> {
  const out = new Headers();
  try {
    const incoming = await headers();
    const xff = incoming.get('x-forwarded-for');
    const ip =
      incoming.get('cf-connecting-ip') ??
      incoming.get('x-real-ip') ??
      (xff ? xff.split(',')[0].trim() : null);
    if (ip) out.set('X-Forwarded-For', ip);
    const agent = incoming.get('user-agent');
    if (agent) out.set('User-Agent', agent);
  } catch {
    // Called outside a request scope (e.g. build time): nothing to forward.
  }
  return out;
}

/** Raw call to Django. No cookies are attached unless a token is passed in. */
export async function backendFetch<T>(path: string, options: FetchOptions = {}): Promise<ApiResponse<T>> {
  const { accessToken, headers: optionHeaders, ...rest } = options;
  // Base every call with the forwarded client IP/UA; explicit headers win.
  const requestHeaders = await clientForwardHeaders();
  for (const [key, value] of new Headers(optionHeaders ?? {})) {
    requestHeaders.set(key, value);
  }
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
 * Server-side call using the access token stored in the HttpOnly cookie.
 *
 * An expired or revoked session sends the visitor back to the sign-in page
 * instead of surfacing a server error. Client IP/UA forwarding is handled by
 * `backendFetch`.
 */
export async function authedFetch<T>(path: string, options: RequestInit = {}): Promise<ApiResponse<T>> {
  const store = await cookies();
  const accessToken = store.get(ACCESS_COOKIE)?.value ?? null;
  if (!accessToken) {
    redirect('/entrar');
  }

  try {
    return await backendFetch<T>(path, { ...options, accessToken });
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
