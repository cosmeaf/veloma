import type { Metadata } from 'next';
import Link from 'next/link';

import { Card, CardHeader, EmptyState, PageHeader } from '@/components/ui';
import { DocumentList } from '@/features/documents/document-list';
import { FolderExplorer, type Folder } from '@/features/documents/folder-explorer';
import { NewFolderForm } from '@/features/documents/new-folder-form';
import { DocumentUploader } from '@/features/documents/uploader';
import { authedData } from '@/lib/api/backend';
import { getCurrentUser, isManager } from '@/lib/auth/session';
import type { ClientSummary, PortalDocument } from '@/types';

export const metadata: Metadata = { title: 'Documentos' };

export default async function StaffDocumentsPage({
  searchParams,
}: {
  searchParams: Promise<{ client?: string; folder?: string }>;
}) {
  const { client: clientId, folder } = await searchParams;
  const user = await getCurrentUser();
  const canDelete = user ? isManager(user) : false;
  const list = await authedData<{ clients: ClientSummary[] }>('/api/client-portal/clients/');

  // Files needing attention are shown regardless of the folder being browsed.
  const flagged = await authedData<{ documents: PortalDocument[] }>('/api/client-portal/documents/');
  const attention = flagged.documents.filter((item) =>
    ['infected', 'quarantined', 'pending_scan', 'rejected'].includes(item.status),
  );

  if (!clientId) {
    return (
      <>
        <PageHeader title="Documentos" description="Escolha um cliente para navegar na estrutura de pastas." />
        {attention.length ? (
          <DocumentList documents={attention} title="A precisar de atenção" description="Em análise, bloqueados ou rejeitados." canDelete={canDelete} />
        ) : null}
        <Card>
          <CardHeader title="Clientes" />
          {list.clients.length === 0 ? (
            <EmptyState title="Sem clientes" />
          ) : (
            <ul className="divide-mist/70 divide-y">
              {list.clients.map((item) => (
                <li key={item.id}>
                  <Link
                    href={`/staff/documentos?client=${item.id}`}
                    className="hover:bg-mist/30 flex items-center justify-between gap-3 px-5 py-3"
                  >
                    <span className="text-navy text-sm font-medium">{item.legal_name}</span>
                    <span className="text-navy/55 text-xs">NIF {item.nif}</span>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </Card>
      </>
    );
  }

  const current = list.clients.find((item) => item.id === clientId);
  const [folders, documents] = await Promise.all([
    authedData<{ folders: Folder[] }>(`/api/client-portal/folders/?client=${clientId}`),
    authedData<{ documents: PortalDocument[] }>(
      `/api/client-portal/documents/?client=${clientId}&folder=${folder ?? 'none'}`,
    ),
  ]);

  return (
    <>
      <PageHeader
        title={current?.legal_name ?? 'Documentos'}
        description="Estrutura de pastas do cliente."
        action={
          <Link href="/staff/documentos" className="text-navy/60 hover:text-navy text-sm hover:underline">
            Trocar de cliente
          </Link>
        }
      />
      <FolderExplorer
        folders={folders.folders}
        documents={documents.documents}
        currentId={folder ?? null}
        basePath="/staff/documentos"
        query={`client=${clientId}`}
        action={<NewFolderForm clientId={clientId} parentId={folder ?? null} />}
        canDelete={canDelete}
      />
      <DocumentUploader clientId={clientId} folderId={folder} />
    </>
  );
}
