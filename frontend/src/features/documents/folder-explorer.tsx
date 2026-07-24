import { ChevronRight, File, FileArchive, Folder, FolderLock, FolderOpen } from 'lucide-react';
import Link from 'next/link';

import { DocumentStatusBadge } from '@/components/status';
import { Badge, Card, CardHeader, EmptyState } from '@/components/ui';
import { DeleteDocumentButton } from '@/features/documents/delete-document-button';
import { DownloadButton } from '@/features/documents/download-button';
import { FolderActions } from '@/features/documents/folder-actions';
import { RenameDocumentButton } from '@/features/documents/rename-document-button';
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

/** Documents older than this drop into the collapsed "Histórico" section. */
const HISTORY_DAYS = 90;

/** Walks the parent chain so the breadcrumb needs no extra requests. The root
 * is the client's own name (its home folder), not a static label. */
export function buildBreadcrumbs(folders: Folder[], currentId: string | null, rootName = 'Início'): Crumb[] {
  const byId = new Map(folders.map((folder) => [folder.id, folder]));
  const crumbs: Crumb[] = [];
  let cursor = currentId ? byId.get(currentId) : undefined;
  while (cursor) {
    crumbs.unshift({ id: cursor.id, name: cursor.name });
    cursor = cursor.parent ? byId.get(cursor.parent) : undefined;
  }
  return [{ id: null, name: rootName }, ...crumbs];
}

export function childrenOf(folders: Folder[], parentId: string | null): Folder[] {
  return folders
    .filter((folder) => (folder.parent ?? null) === parentId && !folder.archived_at)
    .sort((a, b) => a.name.localeCompare(b.name, 'pt'));
}

/**
 * File-explorer view over the client's folder tree, styled like Dropbox: a
 * column header, folders first, then files, with actions revealed on hover.
 *
 * The same component serves staff and clients — each side only receives what
 * its token allows, and `canManage` gates the staff-only actions. Older files
 * fold into a collapsed "Histórico" so the current view stays short.
 */
export function FolderExplorer({
  folders,
  documents,
  currentId,
  basePath,
  query = '',
  action,
  canDelete = false,
  rootName = 'Início',
}: {
  folders: Folder[];
  documents: PortalDocument[];
  currentId: string | null;
  basePath: string;
  query?: string;
  action?: React.ReactNode;
  /** Staff management (rename/delete). Clients only download. */
  canDelete?: boolean;
  /** Label for the root crumb — the client's own name. */
  rootName?: string;
}) {
  const crumbs = buildBreadcrumbs(folders, currentId, rootName);
  const subfolders = childrenOf(folders, currentId);

  const href = (folderId: string | null) => {
    const params = new URLSearchParams(query);
    if (folderId) params.set('folder', folderId);
    else params.delete('folder');
    const search = params.toString();
    return search ? `${basePath}?${search}` : basePath;
  };

  const cutoff = Date.now() - HISTORY_DAYS * 86_400_000;
  const recent = documents.filter((d) => new Date(d.created_at).getTime() >= cutoff);
  const history = documents.filter((d) => new Date(d.created_at).getTime() < cutoff);

  const empty = subfolders.length === 0 && documents.length === 0;

  return (
    <Card className="overflow-hidden">
      <CardHeader
        title="Ficheiros"
        description="Envie, descarregue e organize — como no seu computador."
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

      {empty ? (
        <EmptyState title="Pasta vazia" description="Arraste ficheiros para enviar ou crie uma pasta." />
      ) : (
        <>
          {/* Column header, Explorer-style. */}
          <div className="text-navy/45 border-mist hidden border-b px-5 py-2 text-xs font-medium tracking-wide uppercase sm:flex">
            <span className="flex-1">Nome</span>
            <span className="w-24 text-right">Tamanho</span>
            <span className="w-40 text-right">Modificado</span>
            <span className="w-24" />
          </div>

          <ul className="divide-mist/60 divide-y">
            {subfolders.map((folder) => (
              <FolderRow key={folder.id} folder={folder} href={href(folder.id)} canManage={canDelete} />
            ))}
            {recent.map((document) => (
              <FileRow key={document.id} document={document} canManage={canDelete} />
            ))}
          </ul>

          {history.length ? (
            <details className="group border-mist border-t">
              <summary className="text-navy/60 hover:bg-mist/30 flex cursor-pointer items-center gap-2 px-5 py-3 text-sm font-medium select-none">
                <ChevronRight className="size-4 transition-transform group-open:rotate-90" aria-hidden />
                Histórico ({history.length}) — ficheiros com mais de {HISTORY_DAYS} dias
              </summary>
              <ul className="divide-mist/60 divide-y">
                {history.map((document) => (
                  <FileRow key={document.id} document={document} canManage={canDelete} />
                ))}
              </ul>
            </details>
          ) : null}
        </>
      )}
    </Card>
  );
}

function FolderRow({ folder, href, canManage }: { folder: Folder; href: string; canManage: boolean }) {
  const Icon = folder.visibility === 'staff_only' ? FolderLock : folder.folder_type === 'protocol' ? FolderOpen : Folder;
  return (
    <li className="group hover:bg-mist/30 flex items-center gap-3 px-5 py-2.5">
      <Link href={href} className="flex min-w-0 flex-1 items-center gap-3">
        <Icon className="text-gold-sun size-5 shrink-0" aria-hidden />
        <span className="text-navy truncate text-sm font-medium">{folder.name}</span>
        {folder.visibility === 'staff_only' ? <Badge tone="warning">Interna</Badge> : null}
      </Link>
      <span className="hidden w-24 text-right text-xs text-navy/40 sm:block">—</span>
      <span className="hidden w-40 text-right text-xs text-navy/40 sm:block">—</span>
      <span className="flex w-24 items-center justify-end gap-1">
        {canManage ? (
          <span className="opacity-100 transition-opacity sm:opacity-0 sm:group-hover:opacity-100">
            <FolderActions folderId={folder.id} name={folder.name} />
          </span>
        ) : null}
        <Link href={href} aria-label="Abrir">
          <ChevronRight className="text-navy/30 size-4 shrink-0" aria-hidden />
        </Link>
      </span>
    </li>
  );
}

function FileRow({ document, canManage }: { document: PortalDocument; canManage: boolean }) {
  const Icon = document.category === 'zip' ? FileArchive : File;
  const size = document.current_version ? formatBytes(document.current_version.size) : '—';
  return (
    <li className="group hover:bg-mist/30 flex items-center gap-3 px-5 py-2.5">
      <div className="flex min-w-0 flex-1 items-center gap-3">
        <Icon className="text-navy/40 size-5 shrink-0" aria-hidden />
        <div className="min-w-0">
          <p className="text-navy truncate text-sm font-medium">{document.title}</p>
          <p className="text-navy/50 mt-0.5 truncate text-xs">
            {[document.protocol_number, document.uploader_name_snapshot].filter(Boolean).join(' · ')}
          </p>
          {document.note ? <p className="text-navy/60 mt-0.5 truncate text-xs italic">“{document.note}”</p> : null}
        </div>
      </div>
      <span className="hidden w-24 text-right text-xs text-navy/50 sm:block">{size}</span>
      <span className="hidden w-40 text-right text-xs text-navy/50 sm:block">{formatDateTime(document.created_at)}</span>
      <span className="flex w-24 items-center justify-end gap-1">
        <DocumentStatusBadge status={document.status} />
        {document.status === 'available' ? <DownloadButton documentId={document.id} /> : null}
        {canManage ? (
          <span className="flex gap-1 opacity-100 transition-opacity sm:opacity-0 sm:group-hover:opacity-100">
            <RenameDocumentButton documentId={document.id} title={document.title} />
            <DeleteDocumentButton documentId={document.id} title={document.title} />
          </span>
        ) : null}
      </span>
    </li>
  );
}
