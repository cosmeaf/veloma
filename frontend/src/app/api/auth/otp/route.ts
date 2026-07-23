import { NextResponse } from 'next/server';

import { BackendError, backendFetch } from '@/lib/api/backend';
import { storeTokens } from '@/lib/auth/session';
import type { User } from '@/types';

type VerifyResult = {
  verified: boolean;
  purpose: string;
  access?: string;
  refresh?: string;
  session_id?: string;
  user?: User;
  uid?: string;
  reset_token?: string;
  expires_in?: number;
};

/** Verifies an OTP. For login it stores the tokens; for reset it returns the grant. */
export async function POST(request: Request) {
  const body = (await request.json()) as { challenge_id?: string; code?: string; action?: string };

  try {
    if (body.action === 'resend') {
      const payload = await backendFetch<{ challenge_id: string; expires_at: string; resend_count: number }>(
        '/api/auth/otp/resend/',
        { method: 'POST', body: JSON.stringify({ challenge_id: body.challenge_id }) },
      );
      return NextResponse.json({ success: true, ...payload.data });
    }

    const payload = await backendFetch<VerifyResult>('/api/auth/otp/verify/', {
      method: 'POST',
      body: JSON.stringify({ challenge_id: body.challenge_id, code: body.code }),
    });
    const data = payload.data as VerifyResult;

    if (data.access && data.refresh) {
      await storeTokens({ access: data.access, refresh: data.refresh, session_id: data.session_id });
      return NextResponse.json({ success: true, purpose: data.purpose, user: data.user });
    }

    // Password reset: the opaque grant travels back to the browser only for the
    // duration of the reset form, exactly as the backend contract defines.
    return NextResponse.json({
      success: true,
      purpose: data.purpose,
      uid: data.uid,
      reset_token: data.reset_token,
      expires_in: data.expires_in,
    });
  } catch (error) {
    const status = error instanceof BackendError ? error.status : 502;
    const message = error instanceof Error ? error.message : 'Não foi possível validar o código.';
    return NextResponse.json({ success: false, message }, { status });
  }
}
