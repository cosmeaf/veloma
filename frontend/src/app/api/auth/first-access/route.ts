import { cookies } from 'next/headers';
import { NextResponse } from 'next/server';

import { BackendError, backendFetch } from '@/lib/api/backend';
import { ACCESS_COOKIE } from '@/lib/auth/cookies';
import { clearTokens } from '@/lib/auth/session';

export async function POST(request: Request) {
  const store = await cookies();
  const access = store.get(ACCESS_COOKIE)?.value;
  if (!access) {
    return NextResponse.json({ success: false, message: 'Sessão expirada.' }, { status: 401 });
  }

  const body = await request.json();
  try {
    await backendFetch('/api/auth/first-access/', {
      method: 'POST',
      accessToken: access,
      body: JSON.stringify(body),
    });
    // The backend revoked every session: the cookies are dead weight now.
    await clearTokens();
    return NextResponse.json({ success: true });
  } catch (error) {
    const status = error instanceof BackendError ? error.status : 502;
    const message = error instanceof Error ? error.message : 'Não foi possível concluir o primeiro acesso.';
    return NextResponse.json({ success: false, message }, { status });
  }
}
