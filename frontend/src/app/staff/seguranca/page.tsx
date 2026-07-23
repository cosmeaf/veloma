import type { Metadata } from 'next';

import { SecurityPanel } from '@/features/account/security-panel';
import { authedData } from '@/lib/api/backend';
import { getCurrentUser } from '@/lib/auth/session';
import type { Session } from '@/types';

export const metadata: Metadata = { title: 'Segurança' };

export default async function StaffSecurityPage() {
  const [user, sessions] = await Promise.all([
    getCurrentUser(),
    authedData<{ sessions: Session[] }>('/api/auth/sessions/'),
  ]);

  return <SecurityPanel user={user!} sessions={sessions.sessions} />;
}
