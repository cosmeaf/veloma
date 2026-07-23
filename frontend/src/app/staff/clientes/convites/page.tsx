import type { Metadata } from 'next';
import Link from 'next/link';

import { InvitationStatusBadge } from '@/components/status';
import { Card, CardHeader, EmptyState, PageHeader } from '@/components/ui';
import { ClientTabs } from '@/features/clients/client-tabs';
import { InvitationForm } from '@/features/invitations/invitation-form';
import { InvitationRowActions } from '@/features/invitations/invitation-actions';
import { authedData } from '@/lib/api/backend';
import { MEMBER_ROLES, formatDateTime, label } from '@/lib/utils/format';
import type { ClientSummary, Invitation } from '@/types';

export const metadata: Metadata = { title: 'Convites' };

export default async function StaffInvitationsPage() {
  const [clientList, invitationList] = await Promise.all([
    authedData<{ clients: ClientSummary[] }>('/api/client-portal/clients/'),
    authedData<{ invitations: Invitation[] }>('/api/client-portal/invitations/'),
  ]);
  const active = clientList.clients.filter((c) => c.status !== 'archived');
  const pending = invitationList.invitations.filter((i) => i.status === 'pending');
  const others = invitationList.invitations.filter((i) => i.status !== 'pending');

  return (
    <>
      <PageHeader title="Clientes" description="Empresas acompanhadas pelo escritório." />
      <ClientTabs />

      {/* Send form and pending list side by side on wide screens. */}
      <div className="grid gap-6 lg:grid-cols-2">
        <InvitationForm clients={active.map((c) => ({ id: c.id, legal_name: c.legal_name }))} />

        <Card>
          <CardHeader title="Pendentes" description={`${pending.length} por aceitar.`} />
          {pending.length === 0 ? (
            <EmptyState title="Sem convites pendentes" />
          ) : (
            <ul className="divide-mist/70 divide-y">
              {pending.map((invitation) => (
                <li key={invitation.id} className="flex flex-wrap items-center justify-between gap-3 px-5 py-3">
                  <div>
                    <p className="text-navy text-sm font-medium">{invitation.email}</p>
                    <p className="text-navy/55 mt-0.5 text-xs">
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
      </div>

      <Card>
        <CardHeader title="Histórico" />
        {others.length === 0 ? (
          <EmptyState title="Sem histórico" />
        ) : (
          <ul className="divide-mist/70 divide-y">
            {others.map((invitation) => (
              <li key={invitation.id} className="flex flex-wrap items-center justify-between gap-3 px-5 py-3">
                <div>
                  <p className="text-navy text-sm font-medium">{invitation.email}</p>
                  <p className="text-navy/55 mt-0.5 text-xs">
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
