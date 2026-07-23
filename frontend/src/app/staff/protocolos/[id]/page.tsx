import { ArrowLeft } from 'lucide-react';
import type { Metadata } from 'next';
import Link from 'next/link';
import { notFound } from 'next/navigation';

import { ProtocolStatusBadge } from '@/components/status';
import { Badge, Card, PageHeader } from '@/components/ui';
import { DocumentList } from '@/features/documents/document-list';
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

      <dl className="grid gap-4 sm:grid-cols-3">
        <Card className="p-4">
          <dt className="text-xs tracking-wide text-navy/55 uppercase">Prazo</dt>
          <dd className="mt-1 text-sm font-medium text-navy">{formatDate(protocol.due_date)}</dd>
        </Card>
        <Card className="p-4">
          <dt className="text-xs tracking-wide text-navy/55 uppercase">Competência</dt>
          <dd className="mt-1 text-sm font-medium text-navy">
            {protocol.competence_month && protocol.competence_year
              ? `${String(protocol.competence_month).padStart(2, '0')}/${protocol.competence_year}`
              : '—'}
          </dd>
        </Card>
        <Card className="p-4">
          <dt className="text-xs tracking-wide text-navy/55 uppercase">Concluído em</dt>
          <dd className="mt-1 text-sm font-medium text-navy">{formatDate(protocol.completed_at)}</dd>
        </Card>
      </dl>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="space-y-6">
          <ProtocolActions protocolId={id} status={protocol.status} isManager={user ? isManager(user) : false} />
          <RequirementChecklist requirements={requirements.requirements} />
          {open ? <DocumentUploader protocolId={id} /> : null}
          <DocumentList documents={documents.documents} description="Ficheiros deste protocolo." />
        </div>
        <div className="space-y-6">
          <CommentThread protocolId={id} comments={comments.comments} canComment canWriteInternal />
          <ProtocolTimeline events={timeline.timeline} />
        </div>
      </div>
    </>
  );
}
