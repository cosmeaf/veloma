import type { Metadata } from 'next';
import Link from 'next/link';

import { ProtocolStatusBadge } from '@/components/status';
import { Card, EmptyState, PageHeader } from '@/components/ui';
import { authedData } from '@/lib/api/backend';
import { PROTOCOL_CATEGORIES, formatDate, label } from '@/lib/utils/format';
import type { Protocol } from '@/types';

export const metadata: Metadata = { title: 'Pedidos' };

export default async function ProtocolsPage() {
  const data = await authedData<{ protocols: Protocol[] }>('/api/client-portal/protocols/');

  return (
    <>
      <PageHeader title="Pedidos" description="Cada pedido tem um número e um histórico próprios." />
      <Card>
        {data.protocols.length === 0 ? (
          <EmptyState title="Sem pedidos" />
        ) : (
          <ul className="divide-y divide-mist/70">
            {data.protocols.map((protocol) => (
              <li key={protocol.id}>
                <Link
                  href={`/dashboard/protocolos/${protocol.id}`}
                  className="flex flex-wrap items-center justify-between gap-3 px-5 py-4 hover:bg-mist/30"
                >
                  <div>
                    <p className="text-sm font-medium text-navy">{protocol.title}</p>
                    <p className="mt-0.5 text-xs text-navy/55">
                      {protocol.number} · {label(PROTOCOL_CATEGORIES, protocol.category)}
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
