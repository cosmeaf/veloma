import { DocumentStatusBadge } from '@/components/status';
import { Card, CardHeader, EmptyState } from '@/components/ui';
import { DownloadButton } from '@/features/documents/download-button';
import { formatBytes, formatDateTime } from '@/lib/utils/format';
import type { PortalDocument } from '@/types';

export function DocumentList({
  documents,
  title = 'Documentos',
  description,
}: {
  documents: PortalDocument[];
  title?: string;
  description?: string;
}) {
  return (
    <Card>
      <CardHeader title={title} description={description} />
      {documents.length === 0 ? (
        <EmptyState title="Sem documentos" description="Os ficheiros enviados aparecem aqui." />
      ) : (
        <ul className="divide-y divide-mist/70">
          {documents.map((document) => (
            <li key={document.id} className="flex flex-wrap items-center justify-between gap-3 px-5 py-3">
              <div className="min-w-0">
                <p className="truncate text-sm font-medium text-navy">{document.title}</p>
                <p className="mt-0.5 text-xs text-navy/55">
                  {[
                    document.uploader_name_snapshot,
                    document.current_version ? `v${document.current_version.version_number}` : null,
                    document.current_version ? formatBytes(document.current_version.size) : null,
                    formatDateTime(document.created_at),
                  ]
                    .filter(Boolean)
                    .join(' · ')}
                </p>
                {document.rejection_reason ? (
                  <p className="mt-1 text-xs text-red-600">{document.rejection_reason}</p>
                ) : null}
              </div>
              <div className="flex items-center gap-2">
                <DocumentStatusBadge status={document.status} />
                {document.status === 'available' ? <DownloadButton documentId={document.id} /> : null}
              </div>
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}
