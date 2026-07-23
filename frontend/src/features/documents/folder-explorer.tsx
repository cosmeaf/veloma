import { ChevronRight, Folder, FolderLock, FolderOpen, HardDrive } from 'lucide-react';
import Link from 'next/link';

import { DocumentStatusBadge } from '@/components/status';
import { Badge, Card, CardHeader, EmptyState } from '@/components/ui';
import { DeleteDocumentButton } from '@/features/documents/delete-document-button';
import { DownloadButton } from '@/features/documents/download-button';
import { formatBytes, formatDateTime } from '@/lib/utils/format';
import type { PortalDocument } from '@/types';

export type Folder = {
  id: string;
  client: string;
  parent: string | null;
  name: string;
  slug: string;
  path: string;
  folder_type: string;
  visibility?: 'client_and_staff' | 'staff_only';
  year: number | null;
  month: number | null;
  archived_at: string | null;
};

export type Crumb = { id: string | null; name: string };

/** Walks the parent chain so the breadcrumb needs no extra requests. */
export function buildBreadcrumbs(folders: Folder[], currentId: string | null): Crumb[] {
  const byId = new Map(folders.map((folder) => [folder.id, folder]));
  const crumbs: Crumb[] = [];
  let cursor = currentId ? byId.get(currentId) : undefined;
  while (cursor) {
    crumbs.unshift({ id: cursor.id, name: cursor.name });
    cursor = cursor.parent ? byId.get(cursor.parent) : undefined;
  }
  return [{ id: null, name: 'Raiz' }, ...crumbs];
}

export function childrenOf(folders: Folder[], parentId: string | null): Folder[] {
  return folders
    .filter((folder) => (folder.parent ?? null) === parentId && !folder.archived_at)
    .sort((a, b) => a.name.localeCompare(b.name, 'pt'));
}

/**
 * File-explorer view over the client's folder tree.
 *
 * Used by both areas: the same component renders for staff and for clients,
 * and each side only receives the folders and documents its token allows.
 */
export function FolderExplorer({
  folders,
  documents,
  currentId,
  basePath,
  query = '',
  action,
  canDelete = false,
}: {
  folders: Folder[];
  documents: PortalDocument[];
  currentId: string | null;
  basePath: string;
  query?: string;
  action?: React.ReactNode;
  canDelete?: boolean;
}) {
  const crumbs = buildBreadcrumbs(folders, currentId);
  const subfolders = childrenOf(folders, currentId);

  const href = (folderId: string | null) => {
    const params = new URLSearchParams(query);
    if (folderId) params.set('folder', folderId);
    else params.delete('folder');
    const search = params.toString();
    return search ? `${basePath}?${search}` : basePath;
  };

  return (
    <Card>
      <CardHeader
        title="Pastas"
        description={currentId ? crumbs.map((crumb) => crumb.name).join(' / ') : 'Estrutura de documentos do cliente.'}
        action={action}
      />

      <nav aria-label="Caminho" className="border-mist flex flex-wrap items-center gap-1 border-b px-5 py-2.5 text-sm">
        {crumbs.map((crumb, index) => (
          <span key={crumb.id ?? 'root'} className="flex items-center gap-1">
            {index > 0 ? <ChevronRight className="text-navy/30 size-3.5" aria-hidden /> : null}
            {index === crumbs.length - 1 ? (
              <span className="text-navy font-medium">{crumb.name}</span>
            ) : (
              <Link href={href(crumb.id)} className="text-navy/60 hover:text-navy hover:underline">
                {crumb.name}
              </Link>
            )}
          </span>
        ))}
      </nav>

      {subfolders.length === 0 && documents.length === 0 ? (
        <EmptyState title="Pasta vazia" description="Sem subpastas nem documentos aqui." />
      ) : (
        <ul className="divide-mist/70 divide-y">
          {subfolders.map((folder) => (
            <li key={folder.id}>
              <Link href={href(folder.id)} className="hover:bg-mist/30 flex items-center gap-3 px-5 py-3">
                {folder.visibility === 'staff_only' ? (
                  <FolderLock className="text-navy/50 size-4.5 shrink-0" aria-hidden />
                ) : folder.folder_type === 'protocol' ? (
                  <FolderOpen className="text-gold-sun size-4.5 shrink-0" aria-hidden />
                ) : (
                  <Folder className="text-gold-sun size-4.5 shrink-0" aria-hidden />
                )}
                <span className="text-navy flex-1 text-sm font-medium">{folder.name}</span>
                {folder.visibility === 'staff_only' ? <Badge tone="warning">Interna</Badge> : null}
                <ChevronRight className="text-navy/30 size-4" aria-hidden />
              </Link>
            </li>
          ))}

          {documents.map((document) => (
            <li key={document.id} className="flex flex-wrap items-center justify-between gap-3 px-5 py-3">
              <div className="flex min-w-0 items-center gap-3">
                <HardDrive className="text-navy/40 size-4.5 shrink-0" aria-hidden />
                <div className="min-w-0">
                  <p className="text-navy truncate text-sm font-medium">{document.title}</p>
                  <p className="text-navy/55 mt-0.5 text-xs">
                    {[
                      document.uploader_name_snapshot,
                      document.current_version ? `v${document.current_version.version_number}` : null,
                      document.current_version ? formatBytes(document.current_version.size) : null,
                      formatDateTime(document.created_at),
                    ]
                      .filter(Boolean)
                      .join(' · ')}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <DocumentStatusBadge status={document.status} />
                {document.status === 'available' ? <DownloadButton documentId={document.id} /> : null}
                {canDelete ? <DeleteDocumentButton documentId={document.id} /> : null}
              </div>
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}
