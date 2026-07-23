import { NextResponse } from 'next/server';

import { BackendError, backendFetch } from '@/lib/api/backend';

/** Public endpoint: accepting an invitation is the only way to create an account. */
export async function POST(request: Request) {
  const body = await request.json();
  try {
    const payload = await backendFetch<{ accepted: boolean; email: string; client_name: string }>(
      '/api/client-portal/invitations/accept/',
      { method: 'POST', body: JSON.stringify(body) },
    );
    return NextResponse.json({ success: true, ...payload.data });
  } catch (error) {
    const status = error instanceof BackendError ? error.status : 502;
    const message = error instanceof Error ? error.message : 'Não foi possível concluir o registo.';
    return NextResponse.json({ success: false, message }, { status });
  }
}
