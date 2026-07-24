import { cookies } from 'next/headers';
import { NextResponse } from 'next/server';

import { BACKEND_URL } from '@/lib/api/backend';
import { ACCESS_COOKIE } from '@/lib/auth/cookies';

/**
 * Streams a document straight from the authenticated backend to the browser.
 *
 * Unlike the generic `[...path]` proxy (which buffers text), this forwards the
 * raw body and the download headers, so the file is never held in memory and
 * arrives as an attachment. No public object-storage endpoint is involved.
 */
export async function GET(request: Request, context: { params: Promise<{ id: string }> }) {
  const { id } = await context.params;
  const store = await cookies();
  const access = store.get(ACCESS_COOKIE)?.value;
  if (!access) {
    return NextResponse.json({ success: false, message: 'Sessão expirada.' }, { status: 401 });
  }

  const headers = new Headers({ Authorization: `Bearer ${access}` });
  const clientIp = request.headers.get('x-forwarded-for') ?? request.headers.get('x-real-ip');
  if (clientIp) headers.set('X-Forwarded-For', clientIp);
  const agent = request.headers.get('user-agent');
  if (agent) headers.set('User-Agent', agent);

  const response = await fetch(`${BACKEND_URL}/api/client-portal/documents/${id}/file/`, {
    headers,
    cache: 'no-store',
  });

  if (!response.ok) {
    const text = await response.text();
    return new NextResponse(text, {
      status: response.status,
      headers: { 'Content-Type': response.headers.get('content-type') ?? 'application/json' },
    });
  }

  const forward = new Headers();
  for (const key of ['content-type', 'content-disposition', 'content-length']) {
    const value = response.headers.get(key);
    if (value) forward.set(key, value);
  }
  return new NextResponse(response.body, { status: 200, headers: forward });
}
