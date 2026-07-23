import type { Metadata } from 'next';
import Link from 'next/link';

import { Badge, Card, EmptyState, PageHeader } from '@/components/ui';
import { authedData } from '@/lib/api/backend';
import { formatDate } from '@/lib/utils/format';
import type { ClientSummary } from '@/types';

export const metadata: Metadata = { title: 'Clientes' };

const STATUS_TONE = { active: 'success', deactivated: 'warning', archived: 'neutral' } as const;

export default async function StaffClientsPage() {
  const data = await authedData<{ clients: ClientSummary[] }>('/api/client-portal/clients/');

  return (
    <>
      <PageHeader title="Clientes" description="Empresas acompanhadas pelo escritório." />
      <Card>
        {data.clients.length === 0 ? (
          <EmptyState title="Sem clientes" description="Os clientes criados aparecem aqui." />
        ) : (
          <ul className="divide-y divide-mist/70">
            {data.clients.map((client) => (
              <li key={client.id}>
                <Link
                  href={`/staff/clientes/${client.id}`}
                  className="flex flex-wrap items-center justify-between gap-3 px-5 py-4 hover:bg-mist/30"
                >
                  <div>
                    <p className="text-sm font-medium text-navy">{client.legal_name}</p>
                    <p className="mt-0.5 text-xs text-navy/55">
                      NIF {client.nif} · desde {formatDate(client.created_at)}
                    </p>
                  </div>
                  <Badge tone={STATUS_TONE[client.status as keyof typeof STATUS_TONE] ?? 'neutral'}>
                    {client.status}
                  </Badge>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </Card>
    </>
  );
}
