import { NextResponse, type NextRequest } from 'next/server';

import {
  ACCESS_COOKIE,
  REFRESH_COOKIE,
  SESSION_COOKIE,
  cookieOptions,
  isExpired,
  rolesFromToken,
  secondsUntilExpiry,
} from '@/lib/auth/cookies';

const BACKEND_URL = (process.env.BACKEND_URL ?? 'http://localhost:19080').replace(/\/$/, '');

const STAFF_PREFIX = '/staff';
const CLIENT_PREFIX = '/dashboard';

function isProtected(pathname: string): boolean {
  return pathname.startsWith(STAFF_PREFIX) || pathname.startsWith(CLIENT_PREFIX) || pathname === '/primeiro-acesso';
}

function redirectToLogin(request: NextRequest): NextResponse {
  const url = new URL('/entrar', request.url);
  if (isProtected(request.nextUrl.pathname)) {
    url.searchParams.set('next', request.nextUrl.pathname);
  }
  const response = NextResponse.redirect(url);
  for (const name of [ACCESS_COOKIE, REFRESH_COOKIE, SESSION_COOKIE]) {
    response.cookies.set(name, '', { ...cookieOptions(0), maxAge: 0 });
  }
  return response;
}

/**
 * Refreshes the access token when it is missing or expired.
 *
 * The rotated tokens are written both on the request (so the current render
 * already sees them) and on the response. A single attempt per request avoids
 * refresh loops.
 */
async function refreshTokens(request: NextRequest, refreshToken: string) {
  try {
    const response = await fetch(`${BACKEND_URL}/api/auth/token/refresh/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh: refreshToken }),
      cache: 'no-store',
    });
    if (!response.ok) return null;
    const payload = (await response.json()) as { access?: string; refresh?: string; session_id?: string };
    if (!payload.access) return null;
    return payload;
  } catch {
    return null;
  }
}

export async function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const access = request.cookies.get(ACCESS_COOKIE)?.value;
  const refresh = request.cookies.get(REFRESH_COOKIE)?.value;
  const protectedRoute = isProtected(pathname);

  let activeAccess = access;
  let rotated: { access?: string; refresh?: string; session_id?: string } | null = null;

  if ((!access || isExpired(access)) && refresh) {
    rotated = await refreshTokens(request, refresh);
    if (rotated?.access) {
      activeAccess = rotated.access;
      request.cookies.set(ACCESS_COOKIE, rotated.access);
      if (rotated.refresh) request.cookies.set(REFRESH_COOKIE, rotated.refresh);
    } else if (protectedRoute) {
      return redirectToLogin(request);
    }
  }

  if (protectedRoute && !activeAccess) {
    return redirectToLogin(request);
  }

  // Route-level separation between the two dashboards. The backend still
  // enforces every permission; this only keeps people out of the wrong shell.
  if (activeAccess) {
    const roles = rolesFromToken(activeAccess);
    const staff = roles.includes('STAFF') || roles.includes('STAFF_MANAGER');
    if (pathname.startsWith(STAFF_PREFIX) && !staff) {
      return NextResponse.redirect(new URL('/dashboard', request.url));
    }
    if (pathname.startsWith(CLIENT_PREFIX) && staff) {
      return NextResponse.redirect(new URL('/staff', request.url));
    }
    if (pathname === '/entrar') {
      return NextResponse.redirect(new URL(staff ? '/staff' : '/dashboard', request.url));
    }
  }

  const response = NextResponse.next({ request: { headers: request.headers } });
  if (rotated?.access) {
    response.cookies.set(ACCESS_COOKIE, rotated.access, cookieOptions(secondsUntilExpiry(rotated.access, 900)));
    if (rotated.refresh) {
      response.cookies.set(REFRESH_COOKIE, rotated.refresh, cookieOptions(secondsUntilExpiry(rotated.refresh, 604800)));
    }
    if (rotated.session_id) {
      response.cookies.set(SESSION_COOKIE, rotated.session_id, cookieOptions(secondsUntilExpiry(rotated.refresh ?? rotated.access, 604800)));
    }
  }
  return response;
}

export const config = {
  matcher: ['/dashboard/:path*', '/staff/:path*', '/primeiro-acesso', '/entrar'],
};
