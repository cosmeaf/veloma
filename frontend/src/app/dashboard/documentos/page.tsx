import type { Metadata } from 'next';

import { Card, EmptyState, PageHeader } from '@/components/ui';
import { FolderExplorer, type Folder } from '@/features/documents/folder-explorer';
import { DocumentUploader } from '@/features/documents/uploader';
import { authedData } from '@/lib/api/backend';
import type { ClientSummary, PortalDocument } from '@/types';

export const metadata: Metadata = { title: 'Documentos' };

export default async function DocumentsPage({
  searchParams,
}: {
  searchParams: Promise<{ folder?: string }>;
}) {
  const { folder } = await searchParams;
  const list = await authedData<{ clients: ClientSummary[] }>('/api/client-portal/clients/');
  const client = list.clients[0];

  if (!client) {
    return (
      <>
        <PageHeader title="Documentos" />
        <Card>
          <EmptyState title="Sem empresa associada" description="Contacte o escritório." />
        </Card>
      </>
    );
  }

  const [folders, documents] = await Promise.all([
    authedData<{ folders: Folder[] }>(`/api/client-portal/folders/?client=${client.id}`),
    authedData<{ documents: PortalDocument[] }>(
      `/api/client-portal/documents/?client=${client.id}&folder=${folder ?? 'none'}`,
    ),
  ]);

  return (
    <>
      <PageHeader title="Documentos" description="Navegue pelas pastas da sua empresa." />
      <FolderExplorer
        folders={folders.folders}
        documents={documents.documents}
        currentId={folder ?? null}
        basePath="/dashboard/documentos"
        rootName={client.legal_name}
      />
      <DocumentUploader clientId={client.id} folderId={folder} zipOnly />
    </>
  );
}
