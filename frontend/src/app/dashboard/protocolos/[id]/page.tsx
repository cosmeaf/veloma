import { ArrowLeft } from 'lucide-react';
import type { Metadata } from 'next';
import Link from 'next/link';
import { notFound } from 'next/navigation';

import { ProtocolStatusBadge } from '@/components/status';
import { Card, PageHeader } from '@/components/ui';
import { DocumentList } from '@/features/documents/document-list';
import { DocumentUploader } from '@/features/documents/uploader';
import { CommentThread } from '@/features/protocols/comment-thread';
import { RequirementChecklist } from '@/features/protocols/requirements';
import { ProtocolTimeline } from '@/features/protocols/timeline';
import { BackendError, authedData } from '@/lib/api/backend';
import { PROTOCOL_CATEGORIES, formatDate, label } from '@/lib/utils/format';
import type { Comment, PortalDocument, Protocol, Requirement, TimelineEvent } from '@/types';

export const metadata: Metadata = { title: 'Pedido' };

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

  const [requirements, comments, timeline, documents] = await Promise.all([
    authedData<{ requirements: Requirement[] }>(`/api/client-portal/protocols/${id}/requirements/`),
    authedData<{ comments: Comment[] }>(`/api/client-portal/protocols/${id}/comments/`),
    authedData<{ timeline: TimelineEvent[] }>(`/api/client-portal/protocols/${id}/timeline/`),
    authedData<{ documents: PortalDocument[] }>(`/api/client-portal/documents/?protocol=${id}`),
  ]);

  const open = !['completed', 'cancelled', 'archived'].includes(protocol.status);

  return (
    <>
      <Link href="/dashboard/protocolos" className="inline-flex items-center gap-1.5 text-sm text-navy/55 hover:text-navy">
        <ArrowLeft className="size-4" aria-hidden />
        Pedidos
      </Link>

      <PageHeader
        title={protocol.title}
        description={`${protocol.number} · ${label(PROTOCOL_CATEGORIES, protocol.category)}`}
        action={<ProtocolStatusBadge status={protocol.status} display={protocol.display_status} />}
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
          <dt className="text-xs tracking-wide text-navy/55 uppercase">Aberto em</dt>
          <dd className="mt-1 text-sm font-medium text-navy">{formatDate(protocol.created_at)}</dd>
        </Card>
      </dl>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="space-y-6">
          <RequirementChecklist requirements={requirements.requirements} />
          {open ? <DocumentUploader protocolId={id} zipOnly /> : null}
          <DocumentList documents={documents.documents} description="Ficheiros deste pedido." />
        </div>
        <div className="space-y-6">
          <CommentThread protocolId={id} comments={comments.comments} canComment={open} canWriteInternal={false} />
          <ProtocolTimeline events={timeline.timeline} />
        </div>
      </div>
    </>
  );
}
