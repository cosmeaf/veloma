import { cookies } from 'next/headers';
import { NextResponse } from 'next/server';

import { BackendError, backendFetch } from '@/lib/api/backend';
import { ACCESS_COOKIE } from '@/lib/auth/cookies';

export async function POST(request: Request) {
  const store = await cookies();
  const access = store.get(ACCESS_COOKIE)?.value;
  if (!access) {
    return NextResponse.json({ success: false, message: 'Sessão expirada.' }, { status: 401 });
  }
  const body = await request.json();
  try {
    const payload = await backendFetch('/api/auth/two-factor/', {
      method: 'POST',
      accessToken: access,
      body: JSON.stringify(body),
    });
    return NextResponse.json({ success: true, data: payload.data });
  } catch (error) {
    const status = error instanceof BackendError ? error.status : 502;
    const message = error instanceof Error ? error.message : 'Não foi possível atualizar a definição.';
    return NextResponse.json({ success: false, message }, { status });
  }
}
