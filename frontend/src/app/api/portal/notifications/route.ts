import { cookies } from 'next/headers';
import { NextResponse } from 'next/server';

import { BackendError, backendFetch } from '@/lib/api/backend';
import { ACCESS_COOKIE } from '@/lib/auth/cookies';

async function call(method: 'GET' | 'POST') {
  const store = await cookies();
  const access = store.get(ACCESS_COOKIE)?.value;
  if (!access) return NextResponse.json({ success: false }, { status: 401 });
  try {
    const payload = await backendFetch('/api/auth/notifications/', { method, accessToken: access, body: method === 'POST' ? '{}' : undefined });
    return NextResponse.json({ success: true, data: payload.data });
  } catch (error) {
    const status = error instanceof BackendError ? error.status : 502;
    return NextResponse.json({ success: false }, { status });
  }
}

export async function GET() {
  return call('GET');
}
export async function POST() {
  return call('POST');
}
