import { cookies } from 'next/headers';
import { NextResponse } from 'next/server';

import { BackendError, backendFetch } from '@/lib/api/backend';
import { ACCESS_COOKIE } from '@/lib/auth/cookies';
import { clearTokens } from '@/lib/auth/session';

type Body = {
  action: 'recovery' | 'reset' | 'change';
  email?: string;
  uid?: string;
  reset_token?: string;
  current_password?: string;
  password?: string;
  password2?: string;
};

export async function POST(request: Request) {
  const body = (await request.json()) as Body;

  try {
    if (body.action === 'recovery') {
      const payload = await backendFetch<{ challenge_id: string; expires_in: number }>(
        '/api/auth/password/recovery/',
        { method: 'POST', body: JSON.stringify({ email: body.email }) },
      );
      return NextResponse.json({ success: true, ...payload.data });
    }

    if (body.action === 'reset') {
      await backendFetch('/api/auth/password/reset/', {
        method: 'POST',
        body: JSON.stringify({
          uid: body.uid,
          reset_token: body.reset_token,
          password: body.password,
          password2: body.password2,
        }),
      });
      return NextResponse.json({ success: true });
    }

    const store = await cookies();
    const access = store.get(ACCESS_COOKIE)?.value;
    if (!access) {
      return NextResponse.json({ success: false, message: 'Sessão expirada.' }, { status: 401 });
    }
    await backendFetch('/api/auth/password/change/', {
      method: 'POST',
      accessToken: access,
      body: JSON.stringify({
        current_password: body.current_password,
        password: body.password,
        password2: body.password2,
      }),
    });
    // The backend revokes every session after a password change.
    await clearTokens();
    return NextResponse.json({ success: true, sessions_revoked: true });
  } catch (error) {
    const status = error instanceof BackendError ? error.status : 502;
    const message = error instanceof Error ? error.message : 'Não foi possível concluir o pedido.';
    return NextResponse.json({ success: false, message }, { status });
  }
}
