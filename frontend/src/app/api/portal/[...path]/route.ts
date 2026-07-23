import { cookies } from 'next/headers';
import { NextResponse } from 'next/server';

import { BACKEND_URL } from '@/lib/api/backend';
import { ACCESS_COOKIE } from '@/lib/auth/cookies';

/**
 * Authenticated proxy for client-side calls to `/api/client-portal/`.
 *
 * The browser calls `/api/portal/<path>` without ever holding a token: the
 * access token is read from the HttpOnly cookie and attached here. Only the
 * client portal namespace is reachable through this handler.
 */
async function proxy(request: Request, path: string[], method: string) {
  const store = await cookies();
  const access = store.get(ACCESS_COOKIE)?.value;
  if (!access) {
    return NextResponse.json({ success: false, message: 'Sessão expirada.' }, { status: 401 });
  }

  const target = new URL(`${BACKEND_URL}/api/client-portal/${path.join('/')}/`);
  const incoming = new URL(request.url);
  incoming.searchParams.forEach((value, key) => target.searchParams.set(key, value));

  const headers = new Headers();
  headers.set('Authorization', `Bearer ${access}`);
  // Preserve the real client for rate limiting and auditing on the API side.
  const clientIp = request.headers.get('x-forwarded-for') ?? request.headers.get('x-real-ip');
  if (clientIp) headers.set('X-Forwarded-For', clientIp);
  const agent = request.headers.get('user-agent');
  if (agent) headers.set('User-Agent', agent);

  let body: BodyInit | undefined;
  if (method !== 'GET') {
    const contentType = request.headers.get('content-type') ?? '';
    if (contentType.includes('multipart/form-data')) {
      body = await request.formData();
    } else {
      const text = await request.text();
      body = text || '{}';
      headers.set('Content-Type', 'application/json');
    }
  }

  const response = await fetch(target, { method, headers, body, cache: 'no-store' });
  const text = await response.text();
  return new NextResponse(text, {
    status: response.status,
    headers: { 'Content-Type': response.headers.get('content-type') ?? 'application/json' },
  });
}

type Context = { params: Promise<{ path: string[] }> };

export async function GET(request: Request, context: Context) {
  const { path } = await context.params;
  return proxy(request, path, 'GET');
}

export async function POST(request: Request, context: Context) {
  const { path } = await context.params;
  return proxy(request, path, 'POST');
}

export async function PATCH(request: Request, context: Context) {
  const { path } = await context.params;
  return proxy(request, path, 'PATCH');
}
