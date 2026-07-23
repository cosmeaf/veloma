import { ArrowLeft } from 'lucide-react';
import type { Metadata } from 'next';
import Link from 'next/link';
import { notFound } from 'next/navigation';

import { InvitationStatusBadge, ProtocolStatusBadge } from '@/components/status';
import { Badge, Card, CardHeader, EmptyState, PageHeader } from '@/components/ui';
import { InvitationForm } from '@/features/invitations/invitation-form';
import { BackendError, authedData } from '@/lib/api/backend';
import { MEMBER_ROLES, formatDate, formatDateTime, label } from '@/lib/utils/format';
import type { ClientDetail, Invitation, Member, Protocol } from '@/types';

export const metadata: Metadata = { title: 'Cliente' };

export default async function StaffClientDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;

  let client: ClientDetail;
  try {
    const data = await authedData<{ client: ClientDetail }>(`/api/client-portal/clients/${id}/`);
    client = data.client;
  } catch (error) {
    if (error instanceof BackendError && error.status === 404) notFound();
    throw error;
  }

  const [members, protocols, invitations] = await Promise.all([
    authedData<{ members: Member[] }>(`/api/client-portal/clients/${id}/members/`),
    authedData<{ protocols: Protocol[] }>(`/api/client-portal/protocols/?client=${id}`),
    authedData<{ invitations: Invitation[] }>('/api/client-portal/invitations/'),
  ]);
  const clientInvitations = invitations.invitations.filter((item) => item.client === id);

  return (
    <>
      <Link href="/staff/clientes" className="inline-flex items-center gap-1.5 text-sm text-navy/55 hover:text-navy">
        <ArrowLeft className="size-4" aria-hidden />
        Clientes
      </Link>

      <PageHeader
        title={client.legal_name}
        description={`NIF ${client.nif} · ${client.city || 'Portugal'}`}
        action={<Badge tone={client.status === 'active' ? 'success' : 'warning'}>{client.status}</Badge>}
      />

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader title="Membros" description={`${members.members.length} vínculo(s).`} />
          {members.members.length === 0 ? (
            <EmptyState title="Sem membros" description="Envie um convite para dar acesso." />
          ) : (
            <ul className="divide-y divide-mist/70">
              {members.members.map((member) => (
                <li key={member.id} className="flex flex-wrap items-center justify-between gap-3 px-5 py-3">
                  <div>
                    <p className="text-sm font-medium text-navy">
                      {`${member.first_name} ${member.last_name}`.trim() || member.email}
                    </p>
                    <p className="mt-0.5 text-xs text-navy/55">{member.email}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge>{label(MEMBER_ROLES, member.role)}</Badge>
                    <Badge tone={member.status === 'active' ? 'success' : 'neutral'}>{member.status}</Badge>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </Card>

        <div className="space-y-6">
          <InvitationForm clientId={id} clientName={client.legal_name} />

          <Card>
            <CardHeader title="Convites" />
            {clientInvitations.length === 0 ? (
              <EmptyState title="Sem convites" />
            ) : (
              <ul className="divide-y divide-mist/70">
                {clientInvitations.map((invitation) => (
                  <li key={invitation.id} className="flex flex-wrap items-center justify-between gap-3 px-5 py-3">
                    <div>
                      <p className="text-sm font-medium text-navy">{invitation.email}</p>
                      <p className="mt-0.5 text-xs text-navy/55">
                        {label(MEMBER_ROLES, invitation.role)} · expira {formatDateTime(invitation.expires_at)}
                      </p>
                    </div>
                    <InvitationStatusBadge status={invitation.status} />
                  </li>
                ))}
              </ul>
            )}
          </Card>
        </div>
      </div>

      <Card>
        <CardHeader title="Protocolos" description={`${protocols.protocols.length} no total.`} />
        {protocols.protocols.length === 0 ? (
          <EmptyState title="Sem protocolos" />
        ) : (
          <ul className="divide-y divide-mist/70">
            {protocols.protocols.map((protocol) => (
              <li key={protocol.id}>
                <Link
                  href={`/staff/protocolos/${protocol.id}`}
                  className="flex flex-wrap items-center justify-between gap-3 px-5 py-3 hover:bg-mist/30"
                >
                  <div>
                    <p className="text-sm font-medium text-navy">{protocol.title}</p>
                    <p className="mt-0.5 text-xs text-navy/55">
                      {protocol.number}
                      {protocol.due_date ? ` · prazo ${formatDate(protocol.due_date)}` : ''}
                    </p>
                  </div>
                  <ProtocolStatusBadge status={protocol.status} />
                </Link>
              </li>
            ))}
          </ul>
        )}
      </Card>
    </>
  );
}
