import { cookies } from 'next/headers';
import { NextResponse } from 'next/server';

import { BackendError, backendFetch } from '@/lib/api/backend';
import { ACCESS_COOKIE } from '@/lib/auth/cookies';

export async function POST(_request: Request, context: { params: Promise<{ id: string }> }) {
  const { id } = await context.params;
  const store = await cookies();
  const access = store.get(ACCESS_COOKIE)?.value;
  if (!access) {
    return NextResponse.json({ success: false, message: 'Sessão expirada.' }, { status: 401 });
  }

  try {
    await backendFetch(`/api/auth/sessions/${id}/revoke/`, { method: 'POST', accessToken: access, body: '{}' });
    return NextResponse.json({ success: true });
  } catch (error) {
    const status = error instanceof BackendError ? error.status : 502;
    const message = error instanceof Error ? error.message : 'Não foi possível revogar a sessão.';
    return NextResponse.json({ success: false, message }, { status });
  }
}
