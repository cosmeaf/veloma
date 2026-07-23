'use client';

import { useRouter } from 'next/navigation';
import { useState } from 'react';

import { Button } from '@/components/ui';

export function InvitationRowActions({ invitationId }: { invitationId: string }) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function act(action: 'resend' | 'revoke') {
    setBusy(true);
    setError(null);
    const response = await fetch(`/api/portal/invitations/${invitationId}/${action}`, { method: 'POST' });
    const payload = await response.json().catch(() => ({}));
    setBusy(false);
    if (!response.ok || !payload.success) {
      setError(payload.message ?? 'A operação falhou.');
      return;
    }
    router.refresh();
  }

  return (
    <div className="flex items-center gap-2">
      {error ? <span className="text-xs text-red-600">{error}</span> : null}
      <Button variant="secondary" size="sm" disabled={busy} onClick={() => act('resend')}>
        Reenviar
      </Button>
      <Button variant="danger" size="sm" disabled={busy} onClick={() => act('revoke')}>
        Revogar
      </Button>
    </div>
  );
}
