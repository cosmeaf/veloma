import type { Metadata } from 'next';

import { SecurityPanel } from '@/features/account/security-panel';
import { authedData } from '@/lib/api/backend';
import { getCurrentUser } from '@/lib/auth/session';
import type { AccessEvent, Session } from '@/types';

export const metadata: Metadata = { title: 'Segurança' };

export default async function SecurityPage() {
  const [user, sessions, history] = await Promise.all([
    getCurrentUser(),
    authedData<{ sessions: Session[] }>('/api/auth/sessions/'),
    authedData<{ history: AccessEvent[] }>('/api/auth/access-history/'),
  ]);

  return <SecurityPanel user={user!} sessions={sessions.sessions} history={history.history} />;
}
