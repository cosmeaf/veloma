'use client';

import { Loader2, Trash2 } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useState } from 'react';

import { useToast } from '@/components/toast';
import { Button } from '@/components/ui';

/**
 * Manager-only delete: moves an upload to the recycle bin after a reason prompt.
 * The file stays restorable for 30 days (and recoverable in Dropbox natively).
 */
export function DeleteDocumentButton({ documentId }: { documentId: string }) {
  const router = useRouter();
  const toast = useToast();
  const [busy, setBusy] = useState(false);

  async function remove() {
    const reason = window.prompt('Motivo da eliminação (opcional):', '');
    if (reason === null) return; // cancelled
    setBusy(true);
    const response = await fetch(`/api/portal/documents/${documentId}/delete`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ reason }),
    });
    setBusy(false);
    if (response.ok) {
      toast.success('Documento eliminado. Fica na reciclagem 30 dias.');
      router.refresh();
    } else {
      const payload = await response.json().catch(() => ({}));
      toast.error(payload?.message ?? 'Não foi possível eliminar.');
    }
  }

  return (
    <Button variant="danger" size="sm" onClick={remove} disabled={busy} aria-label="Eliminar">
      {busy ? <Loader2 className="size-4 animate-spin" /> : <Trash2 className="size-4" />}
    </Button>
  );
}
