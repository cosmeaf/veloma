import { cookies } from 'next/headers';
import { NextResponse } from 'next/server';

import { backendFetch } from '@/lib/api/backend';
import { ACCESS_COOKIE, REFRESH_COOKIE } from '@/lib/auth/cookies';
import { clearTokens } from '@/lib/auth/session';

export async function POST(request: Request) {
  const store = await cookies();
  const access = store.get(ACCESS_COOKIE)?.value;
  const refresh = store.get(REFRESH_COOKIE)?.value;
  const body = (await request.json().catch(() => ({}))) as { all?: boolean };

  if (access) {
    try {
      await backendFetch(body.all ? '/api/auth/logout/all/' : '/api/auth/logout/', {
        method: 'POST',
        accessToken: access,
        body: JSON.stringify(body.all ? {} : refresh ? { refresh } : {}),
      });
    } catch {
      // The session may already be revoked; the cookies still have to go.
    }
  }

  await clearTokens();
  return NextResponse.json({ success: true });
}
