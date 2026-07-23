import type { Metadata } from 'next';
import Link from 'next/link';

import { Badge, Card, EmptyState, PageHeader } from '@/components/ui';
import { ClientTabs } from '@/features/clients/client-tabs';
import { NewClientForm } from '@/features/clients/client-form';
import { authedData } from '@/lib/api/backend';
import { formatDate } from '@/lib/utils/format';
import type { ClientSummary, Invitation } from '@/types';

export const metadata: Metadata = { title: 'Clientes' };

const STATUS_TONE = { active: 'success', deactivated: 'warning', archived: 'neutral' } as const;

export default async function StaffClientsPage() {
  const [clients, invitations] = await Promise.all([
    authedData<{ clients: ClientSummary[] }>('/api/client-portal/clients/'),
    authedData<{ invitations: Invitation[] }>('/api/client-portal/invitations/?status=pending'),
  ]);
  const pending = invitations.invitations.filter((item) => item.status === 'pending').length;

  return (
    <>
      <PageHeader title="Clientes" description="Empresas acompanhadas pelo escritório." />
      <ClientTabs />

      {/* Full-width so the expanded form has room. */}
      <NewClientForm />

      {pending ? (
        <Card className="border-gold-high/50 bg-gold-high/10">
          <div className="text-navy px-5 py-3 text-sm">
            {pending} convite(s) por aceitar.{' '}
            <Link href="/staff/clientes/convites" className="font-medium underline">
              Ver convites
            </Link>
          </div>
        </Card>
      ) : null}

      <Card>
        {clients.clients.length === 0 ? (
          <EmptyState title="Sem clientes" description='Comece por "Novo cliente" no topo.' />
        ) : (
          <ul className="divide-mist/70 divide-y">
            {clients.clients.map((client) => (
              <li key={client.id}>
                <Link
                  href={`/staff/clientes/${client.id}`}
                  className="hover:bg-mist/30 flex flex-wrap items-center justify-between gap-3 px-5 py-4"
                >
                  <div>
                    <p className="text-navy text-sm font-medium">{client.legal_name}</p>
                    <p className="text-navy/55 mt-0.5 text-xs">
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
