'use client';

import { Loader2, RotateCcw } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useState } from 'react';

import { useToast } from '@/components/toast';
import { Button } from '@/components/ui';

export function RestoreDocumentButton({ documentId }: { documentId: string }) {
  const router = useRouter();
  const toast = useToast();
  const [busy, setBusy] = useState(false);

  async function restore() {
    setBusy(true);
    const response = await fetch(`/api/portal/documents/${documentId}/restore`, { method: 'POST' });
    setBusy(false);
    if (response.ok) {
      toast.success('Documento restaurado.');
      router.refresh();
    } else {
      const payload = await response.json().catch(() => ({}));
      toast.error(payload?.message ?? 'Não foi possível restaurar.');
    }
  }

  return (
    <Button variant="secondary" size="sm" onClick={restore} disabled={busy}>
      {busy ? <Loader2 className="size-4 animate-spin" /> : <RotateCcw className="size-4" />}
      Restaurar
    </Button>
  );
}
