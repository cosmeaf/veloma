import type { Metadata } from 'next';
import Link from 'next/link';

import { ProtocolStatusBadge } from '@/components/status';
import { Card, CardHeader, EmptyState, PageHeader, StatTile } from '@/components/ui';
import { authedData } from '@/lib/api/backend';
import { formatDate } from '@/lib/utils/format';
import type { Dashboard } from '@/types';

export const metadata: Metadata = { title: 'Resumo' };

export default async function DashboardPage() {
  const data = await authedData<Dashboard>('/api/client-portal/dashboard/');
  const counts = data.protocols;

  return (
    <>
      <PageHeader title="Resumo" description="Estado dos seus pedidos junto do escritório." />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatTile label="Aguardam documentos" value={counts.waiting_documents ?? 0} href="/dashboard/protocolos" />
        <StatTile label="Em análise" value={counts.under_review ?? 0} href="/dashboard/protocolos" />
        <StatTile
          label="Ação necessária"
          value={counts.action_required ?? 0}
          tone={counts.action_required ? 'danger' : 'neutral'}
          href="/dashboard/protocolos"
        />
        <StatTile label="Concluídos" value={counts.completed ?? 0} href="/dashboard/protocolos" />
      </div>

      {data.requirements_pending ? (
        <Card className="border-amber-200 bg-amber-50">
          <div className="px-5 py-4 text-sm text-amber-900">
            Tem <strong>{data.requirements_pending}</strong> documento(s) por enviar.{' '}
            <Link href="/dashboard/protocolos" className="font-medium underline">
              Ver pedidos
            </Link>
          </div>
        </Card>
      ) : null}

      <Card>
        <CardHeader title="Últimas atualizações" />
        {data.recent_protocols.length === 0 ? (
          <EmptyState title="Ainda não existem pedidos" description="O escritório cria aqui os pedidos de documentos." />
        ) : (
          <ul className="divide-y divide-mist/70">
            {data.recent_protocols.map((protocol) => (
              <li key={protocol.id}>
                <Link
                  href={`/dashboard/protocolos/${protocol.id}`}
                  className="flex flex-wrap items-center justify-between gap-3 px-5 py-3 hover:bg-mist/30"
                >
                  <div>
                    <p className="text-sm font-medium text-navy">{protocol.title}</p>
                    <p className="mt-0.5 text-xs text-navy/55">
                      {protocol.number}
                      {protocol.due_date ? ` · prazo ${formatDate(protocol.due_date)}` : ''}
                    </p>
                  </div>
                  <ProtocolStatusBadge status={protocol.status} display={protocol.display_status} />
                </Link>
              </li>
            ))}
          </ul>
        )}
      </Card>
    </>
  );
}
