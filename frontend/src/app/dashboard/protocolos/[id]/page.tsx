import { ArrowLeft } from 'lucide-react';
import type { Metadata } from 'next';
import Link from 'next/link';
import { notFound } from 'next/navigation';

import { PageHeader } from '@/components/ui';
import { FolderExplorer } from '@/features/documents/folder-explorer';
import { DocumentUploader } from '@/features/documents/uploader';
import { BackendError, authedData } from '@/lib/api/backend';
import type { PortalDocument, Protocol } from '@/types';

export const metadata: Metadata = { title: 'Documentos' };

export default async function ProtocolDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;

  let protocol: Protocol;
  try {
    const data = await authedData<{ protocol: Protocol }>(`/api/client-portal/protocols/${id}/`);
    protocol = data.protocol;
  } catch (error) {
    if (error instanceof BackendError && error.status === 404) notFound();
    throw error;
  }

  const documents = await authedData<{ documents: PortalDocument[] }>(
    `/api/client-portal/documents/?protocol=${id}`,
  );

  const open = !['completed', 'cancelled', 'archived'].includes(protocol.status);

  return (
    <>
      <Link href="/dashboard/protocolos" className="text-navy/55 hover:text-navy inline-flex items-center gap-1.5 text-sm">
        <ArrowLeft className="size-4" aria-hidden />
        Voltar
      </Link>

      <PageHeader title={protocol.title} description="Envie e descarregue os ficheiros deste envio." />

      <FolderExplorer
        folders={[]}
        documents={documents.documents}
        currentId={null}
        basePath={`/dashboard/protocolos/${id}`}
        rootName={protocol.number}
        title="Ficheiros"
        description="Ficheiros deste envio."
        showBreadcrumb={false}
      />
      {open ? <DocumentUploader protocolId={id} zipOnly /> : null}
    </>
  );
}
