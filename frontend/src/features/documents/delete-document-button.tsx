'use client';

import { Loader2, Trash2 } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useState } from 'react';

import { useToast } from '@/components/toast';
import { Button } from '@/components/ui';

/**
 * Staff hard delete: permanently removes the file (Dropbox + storage + DB),
 * cascade. No recycle — the removal is final, after a confirmation.
 */
export function DeleteDocumentButton({ documentId, title }: { documentId: string; title?: string }) {
  const router = useRouter();
  const toast = useToast();
  const [busy, setBusy] = useState(false);

  async function remove() {
    if (!window.confirm(`Eliminar definitivamente ${title ? `"${title}"` : 'este documento'}? Esta ação não pode ser anulada.`)) {
      return;
    }
    setBusy(true);
    const response = await fetch(`/api/portal/documents/${documentId}/delete`, { method: 'POST' });
    setBusy(false);
    if (response.ok) {
      toast.success('Documento eliminado.');
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
