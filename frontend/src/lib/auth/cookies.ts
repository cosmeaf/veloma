/**
 * Cookie contract for the BFF.
 *
 * Tokens live only in HttpOnly cookies written by Route Handlers and the
 * middleware. They are never sent to the browser as JSON and never touch
 * localStorage, sessionStorage or any client-side global.
 */
export const ACCESS_COOKIE = 'veloma_access';
export const REFRESH_COOKIE = 'veloma_refresh';
export const SESSION_COOKIE = 'veloma_session';

const isProduction = process.env.NODE_ENV === 'production';

export type CookieOptions = {
  httpOnly: boolean;
  secure: boolean;
  sameSite: 'lax' | 'strict' | 'none';
  path: string;
  maxAge: number;
};

export function cookieOptions(maxAgeSeconds: number): CookieOptions {
  return {
    httpOnly: true,
    secure: isProduction,
    sameSite: 'lax',
    path: '/',
    maxAge: maxAgeSeconds,
  };
}

/** Seconds until a JWT expires, floored at zero. Signature is not verified here. */
export function secondsUntilExpiry(token: string, fallback: number): number {
  const payload = decodeJwt(token);
  if (!payload?.exp) return fallback;
  const remaining = payload.exp - Math.floor(Date.now() / 1000);
  return remaining > 0 ? remaining : 0;
}

export type JwtPayload = {
  exp?: number;
  user_id?: string | number;
  session_id?: string;
  roles?: string[];
};

/**
 * Reads the JWT payload without verifying it. Used only for routing hints and
 * expiry checks; every authorisation decision is made by the Django backend.
 */
export function decodeJwt(token: string): JwtPayload | null {
  try {
    const part = token.split('.')[1];
    if (!part) return null;
    const normalised = part.replace(/-/g, '+').replace(/_/g, '/');
    const padded = normalised.padEnd(normalised.length + ((4 - (normalised.length % 4)) % 4), '=');
    const json =
      typeof atob === 'function'
        ? atob(padded)
        : Buffer.from(padded, 'base64').toString('binary');
    return JSON.parse(json) as JwtPayload;
  } catch {
    return null;
  }
}

export function isExpired(token: string, skewSeconds = 15): boolean {
  const payload = decodeJwt(token);
  if (!payload?.exp) return true;
  return payload.exp - skewSeconds <= Math.floor(Date.now() / 1000);
}

export function rolesFromToken(token: string): string[] {
  return decodeJwt(token)?.roles ?? [];
}
