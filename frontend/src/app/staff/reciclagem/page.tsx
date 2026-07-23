import type { Metadata } from 'next';

import { Alert, Card, CardHeader, EmptyState, PageHeader } from '@/components/ui';
import { RestoreDocumentButton } from '@/features/documents/restore-document-button';
import { authedData } from '@/lib/api/backend';
import { formatDateTime } from '@/lib/utils/format';

export const metadata: Metadata = { title: 'Reciclagem' };

type RecycledDocument = {
  id: string;
  title: string;
  client_name: string;
  protocol_number: string | null;
  deleted_at: string | null;
  deleted_by_name_snapshot: string;
  deletion_reason: string;
  purge_after: string | null;
};

export default async function RecyclePage() {
  const data = await authedData<{ documents: RecycledDocument[] }>('/api/client-portal/recycle/');

  return (
    <>
      <PageHeader
        title="Reciclagem"
        description="Documentos eliminados pela equipa. Restauráveis durante 30 dias."
      />
      <Alert tone="info">
        Os ficheiros continuam recuperáveis no Dropbox (ficheiros eliminados) durante 30 dias. Ao fim desse prazo são
        removidos definitivamente; o registo de quem eliminou permanece como prova.
      </Alert>
      <Card>
        <CardHeader title="Eliminados" description={`${data.documents.length} documento(s).`} />
        {data.documents.length === 0 ? (
          <EmptyState title="Reciclagem vazia" description="Nada foi eliminado recentemente." />
        ) : (
          <ul className="divide-mist/70 divide-y">
            {data.documents.map((document) => (
              <li key={document.id} className="flex flex-wrap items-center justify-between gap-3 px-5 py-3">
                <div className="min-w-0">
                  <p className="text-navy truncate text-sm font-medium">{document.title}</p>
                  <p className="text-navy/55 mt-0.5 text-xs">
                    {[
                      document.client_name,
                      document.protocol_number,
                      document.deleted_by_name_snapshot ? `eliminado por ${document.deleted_by_name_snapshot}` : null,
                      document.deleted_at ? formatDateTime(document.deleted_at) : null,
                    ]
                      .filter(Boolean)
                      .join(' · ')}
                  </p>
                  {document.deletion_reason ? (
                    <p className="text-navy/55 mt-0.5 text-xs italic">“{document.deletion_reason}”</p>
                  ) : null}
                  {document.purge_after ? (
                    <p className="mt-0.5 text-xs text-red-600">
                      Remoção definitiva em {formatDateTime(document.purge_after)}
                    </p>
                  ) : null}
                </div>
                <RestoreDocumentButton documentId={document.id} />
              </li>
            ))}
          </ul>
        )}
      </Card>
    </>
  );
}
