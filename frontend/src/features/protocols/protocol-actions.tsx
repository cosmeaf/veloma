'use client';

import { Loader2 } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useState } from 'react';

import { Alert, Button, Card, CardHeader, Field, Input, Select } from '@/components/ui';
import { PROTOCOL_STATUS } from '@/lib/utils/format';

/** Only transitions the backend accepts are offered; it re-validates anyway. */
const NEXT_STATUS: Record<string, string[]> = {
  draft: ['waiting_documents', 'cancelled'],
  waiting_documents: ['documents_received', 'cancelled'],
  documents_received: ['under_review', 'action_required'],
  under_review: ['action_required', 'processing', 'completed'],
  action_required: ['documents_received', 'under_review'],
  processing: ['completed', 'action_required'],
  completed: ['archived', 'under_review'],
  cancelled: [],
  archived: [],
};

export function ProtocolActions({
  protocolId,
  status,
  isManager,
}: {
  protocolId: string;
  status: string;
  isManager: boolean;
}) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [requirement, setRequirement] = useState('');

  const options = (NEXT_STATUS[status] ?? []).filter(
    (target) => !(status === 'completed' && target === 'under_review' && !isManager),
  );

  async function call(path: string, body: Record<string, unknown>) {
    setBusy(true);
    setError(null);
    const response = await fetch(`/api/portal/${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    const payload = await response.json().catch(() => ({}));
    setBusy(false);
    if (!response.ok || !payload.success) {
      setError(payload.message ?? 'A operação falhou.');
      return false;
    }
    router.refresh();
    return true;
  }

  return (
    <Card>
      <CardHeader title="Ações" description="Alterar estado e pedir documentos." />
      <div className="space-y-4 px-5 py-4">
        {error ? <Alert>{error}</Alert> : null}

        {options.length ? (
          <div className="flex flex-wrap gap-2">
            {options.map((target) => (
              <Button
                key={target}
                variant="secondary"
                size="sm"
                disabled={busy}
                onClick={() => call(`protocols/${protocolId}/transition`, { status: target })}
              >
                {busy ? <Loader2 className="size-4 animate-spin" /> : null}
                {PROTOCOL_STATUS[target] ?? target}
                {status === 'completed' && target === 'under_review' ? ' (reabrir)' : ''}
              </Button>
            ))}
          </div>
        ) : (
          <p className="text-sm text-navy/55">Este protocolo já está fechado.</p>
        )}

        <form
          className="flex items-end gap-2"
          onSubmit={async (event) => {
            event.preventDefault();
            if (!requirement.trim()) return;
            const ok = await call(`protocols/${protocolId}/requirements`, { title: requirement });
            if (ok) setRequirement('');
          }}
        >
          <div className="flex-1">
            <Field label="Solicitar documento">
              <Input
                value={requirement}
                onChange={(event) => setRequirement(event.target.value)}
                placeholder="Ex.: Extrato bancário de julho"
              />
            </Field>
          </div>
          <Button type="submit" size="sm" disabled={busy || !requirement.trim()}>
            Pedir
          </Button>
        </form>
      </div>
    </Card>
  );
}

export function ProtocolStatusSelect({ value, onChange }: { value: string; onChange: (value: string) => void }) {
  return (
    <Select value={value} onChange={(event) => onChange(event.target.value)}>
      {Object.entries(PROTOCOL_STATUS).map(([key, text]) => (
        <option key={key} value={key}>
          {text}
        </option>
      ))}
    </Select>
  );
}
