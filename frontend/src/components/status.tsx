import { Badge, type Tone } from '@/components/ui';
import { DOCUMENT_STATUS, INVITATION_STATUS, PROTOCOL_STATUS, REQUIREMENT_STATUS, label } from '@/lib/utils/format';

const PROTOCOL_TONES: Record<string, Tone> = {
  draft: 'neutral',
  waiting_documents: 'warning',
  documents_received: 'info',
  under_review: 'info',
  action_required: 'danger',
  processing: 'info',
  completed: 'success',
  cancelled: 'neutral',
  archived: 'neutral',
};

const DOCUMENT_TONES: Record<string, Tone> = {
  pending_scan: 'warning',
  available: 'success',
  infected: 'danger',
  quarantined: 'danger',
  rejected: 'danger',
  archived: 'neutral',
};

const REQUIREMENT_TONES: Record<string, Tone> = {
  pending: 'warning',
  uploaded: 'info',
  accepted: 'success',
  rejected: 'danger',
  waived: 'neutral',
};

const INVITATION_TONES: Record<string, Tone> = {
  pending: 'warning',
  accepted: 'success',
  expired: 'neutral',
  revoked: 'danger',
  cancelled: 'neutral',
};

/** Shows the client-facing wording when the API sends `display_status`. */
export function ProtocolStatusBadge({ status, display }: { status: string; display?: string }) {
  return <Badge tone={PROTOCOL_TONES[status] ?? 'neutral'}>{display ?? label(PROTOCOL_STATUS, status)}</Badge>;
}

export function DocumentStatusBadge({ status }: { status: string }) {
  return <Badge tone={DOCUMENT_TONES[status] ?? 'neutral'}>{label(DOCUMENT_STATUS, status)}</Badge>;
}

export function RequirementStatusBadge({ status }: { status: string }) {
  return <Badge tone={REQUIREMENT_TONES[status] ?? 'neutral'}>{label(REQUIREMENT_STATUS, status)}</Badge>;
}

export function InvitationStatusBadge({ status }: { status: string }) {
  return <Badge tone={INVITATION_TONES[status] ?? 'neutral'}>{label(INVITATION_STATUS, status)}</Badge>;
}
