import { ArrowLeft } from 'lucide-react';
import type { Metadata } from 'next';
import Link from 'next/link';
import { notFound } from 'next/navigation';

import { ProtocolStatusBadge } from '@/components/status';
import { Badge, Card, PageHeader } from '@/components/ui';
import { FolderExplorer } from '@/features/documents/folder-explorer';
import { DocumentUploader } from '@/features/documents/uploader';
import { CommentThread } from '@/features/protocols/comment-thread';
import { ProtocolActions } from '@/features/protocols/protocol-actions';
import { RequirementChecklist } from '@/features/protocols/requirements';
import { ProtocolTimeline } from '@/features/protocols/timeline';
import { BackendError, authedData } from '@/lib/api/backend';
import { getCurrentUser, isManager } from '@/lib/auth/session';
import { PRIORITIES, PROTOCOL_CATEGORIES, formatDate, label } from '@/lib/utils/format';
import type { Comment, PortalDocument, Protocol, Requirement, TimelineEvent } from '@/types';

export const metadata: Metadata = { title: 'Protocolo' };

export default async function StaffProtocolDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;

  let protocol: Protocol;
  try {
    const data = await authedData<{ protocol: Protocol }>(`/api/client-portal/protocols/${id}/`);
    protocol = data.protocol;
  } catch (error) {
    if (error instanceof BackendError && error.status === 404) notFound();
    throw error;
  }

  const [user, requirements, comments, timeline, documents] = await Promise.all([
    getCurrentUser(),
    authedData<{ requirements: Requirement[] }>(`/api/client-portal/protocols/${id}/requirements/`),
    authedData<{ comments: Comment[] }>(`/api/client-portal/protocols/${id}/comments/`),
    authedData<{ timeline: TimelineEvent[] }>(`/api/client-portal/protocols/${id}/timeline/`),
    authedData<{ documents: PortalDocument[] }>(`/api/client-portal/documents/?protocol=${id}`),
  ]);

  const open = !['completed', 'cancelled', 'archived'].includes(protocol.status);

  // Only surface metadata that is actually filled — empty "—" fields are noise.
  const competence =
    protocol.competence_month && protocol.competence_year
      ? `${String(protocol.competence_month).padStart(2, '0')}/${protocol.competence_year}`
      : null;
  const meta = [
    { label: 'Prazo', value: protocol.due_date ? formatDate(protocol.due_date) : null },
    { label: 'Competência', value: competence },
    { label: 'Concluído', value: protocol.completed_at ? formatDate(protocol.completed_at) : null },
  ].filter((item) => item.value);

  return (
    <>
      <Link href="/staff/protocolos" className="inline-flex items-center gap-1.5 text-sm text-navy/55 hover:text-navy">
        <ArrowLeft className="size-4" aria-hidden />
        Protocolos
      </Link>

      <PageHeader
        title={protocol.title}
        description={`${protocol.number} · ${protocol.client_name} · ${label(PROTOCOL_CATEGORIES, protocol.category)}`}
        action={
          <div className="flex items-center gap-2">
            <Badge tone={protocol.priority === 'urgent' ? 'danger' : 'neutral'}>
              {label(PRIORITIES, protocol.priority)}
            </Badge>
            <ProtocolStatusBadge status={protocol.status} />
          </div>
        }
      />

      {protocol.description ? (
        <Card>
          <p className="px-5 py-4 text-sm whitespace-pre-wrap text-navy/80">{protocol.description}</p>
        </Card>
      ) : null}

      {meta.length ? (
        <dl className="flex flex-wrap gap-x-8 gap-y-1 text-sm">
          {meta.map((item) => (
            <div key={item.label} className="flex items-baseline gap-2">
              <dt className="text-navy/50">{item.label}</dt>
              <dd className="font-medium text-navy">{item.value}</dd>
            </div>
          ))}
        </dl>
      ) : null}

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          <FolderExplorer
            folders={[]}
            documents={documents.documents}
            currentId={null}
            basePath={`/staff/protocolos/${id}`}
            rootName={protocol.number}
            title="Ficheiros"
            description="Ficheiros deste protocolo."
            showBreadcrumb={false}
            canDelete
          />
          {open ? <DocumentUploader protocolId={id} /> : null}
          <CommentThread protocolId={id} comments={comments.comments} canComment canWriteInternal />
        </div>
        <div className="space-y-6">
          <ProtocolActions protocolId={id} status={protocol.status} isManager={user ? isManager(user) : false} />
          {requirements.requirements.length ? (
            <RequirementChecklist requirements={requirements.requirements} />
          ) : null}
          <ProtocolTimeline events={timeline.timeline} />
        </div>
      </div>
    </>
  );
}
