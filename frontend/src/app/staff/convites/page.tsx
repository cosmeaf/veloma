import type { Metadata } from 'next';
import Link from 'next/link';

import { InvitationStatusBadge } from '@/components/status';
import { Card, CardHeader, EmptyState, PageHeader } from '@/components/ui';
import { InvitationRowActions } from '@/features/invitations/invitation-actions';
import { authedData } from '@/lib/api/backend';
import { MEMBER_ROLES, formatDateTime, label } from '@/lib/utils/format';
import type { Invitation } from '@/types';

export const metadata: Metadata = { title: 'Convites' };

export default async function StaffInvitationsPage() {
  const data = await authedData<{ invitations: Invitation[] }>('/api/client-portal/invitations/');
  const pending = data.invitations.filter((item) => item.status === 'pending');
  const others = data.invitations.filter((item) => item.status !== 'pending');

  return (
    <>
      <PageHeader title="Convites" description="As contas de cliente só nascem de um convite." />

      <Card>
        <CardHeader title="Pendentes" description={`${pending.length} por aceitar.`} />
        {pending.length === 0 ? (
          <EmptyState title="Sem convites pendentes" description="Convide membros a partir da ficha do cliente." />
        ) : (
          <ul className="divide-y divide-mist/70">
            {pending.map((invitation) => (
              <li key={invitation.id} className="flex flex-wrap items-center justify-between gap-3 px-5 py-3">
                <div>
                  <p className="text-sm font-medium text-navy">{invitation.email}</p>
                  <p className="mt-0.5 text-xs text-navy/55">
                    <Link href={`/staff/clientes/${invitation.client}`} className="hover:underline">
                      {invitation.client_name}
                    </Link>
                    {` · ${label(MEMBER_ROLES, invitation.role)} · expira ${formatDateTime(invitation.expires_at)}`}
                  </p>
                </div>
                <InvitationRowActions invitationId={invitation.id} />
              </li>
            ))}
          </ul>
        )}
      </Card>

      <Card>
        <CardHeader title="Histórico" />
        {others.length === 0 ? (
          <EmptyState title="Sem histórico" />
        ) : (
          <ul className="divide-y divide-mist/70">
            {others.map((invitation) => (
              <li key={invitation.id} className="flex flex-wrap items-center justify-between gap-3 px-5 py-3">
                <div>
                  <p className="text-sm font-medium text-navy">{invitation.email}</p>
                  <p className="mt-0.5 text-xs text-navy/55">
                    {invitation.client_name} · {label(MEMBER_ROLES, invitation.role)}
                  </p>
                </div>
                <InvitationStatusBadge status={invitation.status} />
              </li>
            ))}
          </ul>
        )}
      </Card>
    </>
  );
}
