import { NextResponse } from 'next/server';

import { BackendError, backendFetch } from '@/lib/api/backend';
import { storeTokens } from '@/lib/auth/session';
import type { User } from '@/types';

type LoginResult = {
  requires_otp: boolean;
  challenge_id?: string;
  expires_at?: string;
  access?: string;
  refresh?: string;
  session_id?: string;
  user?: User;
};

export async function POST(request: Request) {
  const body = (await request.json()) as { email?: string; password?: string };
  if (!body.email || !body.password) {
    return NextResponse.json({ success: false, message: 'Indique o e-mail e a palavra-passe.' }, { status: 400 });
  }

  try {
    const payload = await backendFetch<LoginResult>('/api/auth/login/', {
      method: 'POST',
      body: JSON.stringify({ email: body.email, password: body.password }),
    });
    const data = payload.data as LoginResult;

    if (data.requires_otp) {
      return NextResponse.json({
        success: true,
        requires_otp: true,
        challenge_id: data.challenge_id,
        expires_at: data.expires_at,
      });
    }

    // Tokens stop here: they go into HttpOnly cookies and never reach the client.
    await storeTokens({ access: data.access!, refresh: data.refresh!, session_id: data.session_id });
    return NextResponse.json({ success: true, requires_otp: false, user: data.user });
  } catch (error) {
    const status = error instanceof BackendError ? error.status : 500;
    const message = error instanceof Error ? error.message : 'Não foi possível autenticar.';
    return NextResponse.json({ success: false, message }, { status: status === 500 ? 502 : status });
  }
}
