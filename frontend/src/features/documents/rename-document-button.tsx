'use client';

import { Loader2, Pencil } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useState } from 'react';

import { useToast } from '@/components/toast';
import { Button } from '@/components/ui';

/** Staff: rename a document (Explorer-style). */
export function RenameDocumentButton({ documentId, title }: { documentId: string; title: string }) {
  const router = useRouter();
  const toast = useToast();
  const [busy, setBusy] = useState(false);

  async function rename() {
    const next = window.prompt('Novo nome do documento:', title);
    if (next === null) return;
    if (!next.trim() || next.trim() === title) return;
    setBusy(true);
    const response = await fetch(`/api/portal/documents/${documentId}/rename`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title: next.trim() }),
    });
    setBusy(false);
    if (response.ok) {
      toast.success('Documento renomeado.');
      router.refresh();
    } else {
      const payload = await response.json().catch(() => ({}));
      toast.error(payload?.message ?? 'Não foi possível renomear.');
    }
  }

  return (
    <Button variant="secondary" size="sm" onClick={rename} disabled={busy} aria-label="Renomear">
      {busy ? <Loader2 className="size-4 animate-spin" /> : <Pencil className="size-4" />}
    </Button>
  );
}
