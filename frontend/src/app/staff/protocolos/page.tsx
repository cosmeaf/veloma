import type { Metadata } from 'next';
import Link from 'next/link';

import { ProtocolStatusBadge } from '@/components/status';
import { Badge, Card, EmptyState, PageHeader } from '@/components/ui';
import { authedData } from '@/lib/api/backend';
import { PRIORITIES, PROTOCOL_CATEGORIES, formatDate, label } from '@/lib/utils/format';
import type { Protocol } from '@/types';

export const metadata: Metadata = { title: 'Protocolos' };

export default async function StaffProtocolsPage({
  searchParams,
}: {
  searchParams: Promise<{ status?: string }>;
}) {
  const { status } = await searchParams;
  const query = status ? `?status=${encodeURIComponent(status)}` : '';
  const data = await authedData<{ protocols: Protocol[] }>(`/api/client-portal/protocols/${query}`);

  return (
    <>
      <PageHeader title="Protocolos" description="Pedidos em curso na sua carteira." />
      <Card>
        {data.protocols.length === 0 ? (
          <EmptyState title="Sem protocolos" />
        ) : (
          <ul className="divide-y divide-mist/70">
            {data.protocols.map((protocol) => (
              <li key={protocol.id}>
                <Link
                  href={`/staff/protocolos/${protocol.id}`}
                  className="flex flex-wrap items-center justify-between gap-3 px-5 py-4 hover:bg-mist/30"
                >
                  <div>
                    <p className="text-sm font-medium text-navy">{protocol.title}</p>
                    <p className="mt-0.5 text-xs text-navy/55">
                      {protocol.number} · {protocol.client_name} · {label(PROTOCOL_CATEGORIES, protocol.category)}
                      {protocol.due_date ? ` · prazo ${formatDate(protocol.due_date)}` : ''}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    {protocol.priority !== 'normal' ? (
                      <Badge tone={protocol.priority === 'urgent' ? 'danger' : 'warning'}>
                        {label(PRIORITIES, protocol.priority)}
                      </Badge>
                    ) : null}
                    <ProtocolStatusBadge status={protocol.status} />
                  </div>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </Card>
    </>
  );
}
