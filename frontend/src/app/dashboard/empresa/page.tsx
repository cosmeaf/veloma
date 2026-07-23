import type { Metadata } from 'next';

import { Badge } from '@/components/ui';
import { Card, CardHeader, EmptyState, PageHeader } from '@/components/ui';
import { authedData } from '@/lib/api/backend';
import { MEMBER_ROLES, label } from '@/lib/utils/format';
import type { ClientDetail, ClientSummary, Member } from '@/types';

export const metadata: Metadata = { title: 'Empresa' };

export default async function CompanyPage() {
  const list = await authedData<{ clients: ClientSummary[] }>('/api/client-portal/clients/');
  const first = list.clients[0];

  if (!first) {
    return (
      <>
        <PageHeader title="Empresa" />
        <Card>
          <EmptyState title="Sem empresa associada" description="Contacte o escritório para regularizar o acesso." />
        </Card>
      </>
    );
  }

  const [detail, members] = await Promise.all([
    authedData<{ client: ClientDetail }>(`/api/client-portal/clients/${first.id}/`),
    authedData<{ members: Member[] }>(`/api/client-portal/clients/${first.id}/members/`),
  ]);
  const client = detail.client;

  const rows: Array<[string, string]> = [
    ['Denominação', client.legal_name],
    ['Nome comercial', client.commercial_name || '—'],
    ['NIF', client.nif],
    ['Atividade', client.activity_description || '—'],
    ['E-mail', client.email || '—'],
    ['Telefone', client.phone || '—'],
    ['Morada', [client.address_line, client.postal_code, client.city].filter(Boolean).join(', ') || '—'],
  ];

  return (
    <>
      <PageHeader
        title={client.legal_name}
        description={`NIF ${client.nif}`}
        action={<Badge tone={client.status === 'active' ? 'success' : 'warning'}>{client.status}</Badge>}
      />

      <div className="grid items-start gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader title="Dados da empresa" description="Para alterações, fale com o escritório." />
          <dl className="divide-mist/70 divide-y">
            {rows.map(([term, value]) => (
              <div key={term} className="flex flex-wrap justify-between gap-2 px-5 py-3">
                <dt className="text-navy/55 text-sm">{term}</dt>
                <dd className="text-navy text-sm font-medium">{value}</dd>
              </div>
            ))}
          </dl>
        </Card>

        <Card>
          <CardHeader title="Membros" description="Quem tem acesso a esta área." />
          <ul className="divide-mist/70 divide-y">
            {members.members.map((member) => (
              <li key={member.id} className="flex flex-wrap items-center justify-between gap-3 px-5 py-3">
                <div>
                  <p className="text-navy text-sm font-medium">
                    {`${member.first_name} ${member.last_name}`.trim() || member.email}
                  </p>
                  <p className="text-navy/55 mt-0.5 text-xs">{member.email}</p>
                </div>
                <Badge>{label(MEMBER_ROLES, member.role)}</Badge>
              </li>
            ))}
          </ul>
        </Card>
      </div>
    </>
  );
}
