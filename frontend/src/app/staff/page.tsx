import type { Metadata } from 'next';
import Link from 'next/link';

import { ProtocolStatusBadge } from '@/components/status';
import { Card, CardHeader, EmptyState, PageHeader, StatTile } from '@/components/ui';
import { TwoFactorBanner } from '@/features/account/two-factor-banner';
import { authedData } from '@/lib/api/backend';
import { getCurrentUser } from '@/lib/auth/session';
import { formatDate } from '@/lib/utils/format';
import type { Dashboard } from '@/types';

export const metadata: Metadata = { title: 'Resumo da equipa' };

export default async function StaffDashboardPage() {
  const [data, user] = await Promise.all([
    authedData<Dashboard>('/api/client-portal/dashboard/'),
    getCurrentUser(),
  ]);
  const counts = data.protocols;
  const staff = data.staff;

  return (
    <>
      <PageHeader title="Resumo" description="Carteira de clientes e trabalho em curso." />
      <TwoFactorBanner enabled={Boolean(user?.two_factor_email)} href="/staff/seguranca" />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatTile label="Aguardam cliente" value={counts.waiting_documents ?? 0} href="/staff/protocolos?status=waiting_documents" />
        <StatTile label="Para analisar" value={counts.documents_received ?? 0} href="/staff/protocolos?status=documents_received" />
        <StatTile label="Em análise" value={counts.under_review ?? 0} href="/staff/protocolos?status=under_review" />
        <StatTile label="Atrasados" value={staff?.overdue ?? 0} tone={staff?.overdue ? 'danger' : 'neutral'} href="/staff/protocolos" />
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatTile label="Clientes" value={staff?.clients ?? 0} href="/staff/clientes" />
        <StatTile label="Uploads em análise" value={staff?.pending_scan ?? 0} href="/staff/documentos" />
        <StatTile
          label="Em quarentena"
          value={staff?.quarantined ?? 0}
          tone={staff?.quarantined ? 'danger' : 'neutral'}
          href="/staff/documentos"
        />
        <StatTile label="Convites pendentes" value={staff?.pending_invitations ?? 0} href="/staff/clientes/convites" />
      </div>

      <Card>
        <CardHeader title="Protocolos recentes" action={<Link href="/staff/protocolos" className="text-sm font-medium text-navy hover:underline">Ver todos</Link>} />
        {data.recent_protocols.length === 0 ? (
          <EmptyState title="Sem protocolos" />
        ) : (
          <ul className="divide-y divide-mist/70">
            {data.recent_protocols.map((protocol) => (
              <li key={protocol.id}>
                <Link
                  href={`/staff/protocolos/${protocol.id}`}
                  className="flex flex-wrap items-center justify-between gap-3 px-5 py-3 hover:bg-mist/30"
                >
                  <div>
                    <p className="text-sm font-medium text-navy">{protocol.title}</p>
                    <p className="mt-0.5 text-xs text-navy/55">
                      {protocol.number} · {protocol.client_name}
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
