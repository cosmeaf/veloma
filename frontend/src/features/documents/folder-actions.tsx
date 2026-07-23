'use client';

import { Loader2, Pencil, Trash2 } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useState } from 'react';

import { useToast } from '@/components/toast';
import { Button } from '@/components/ui';

/** Staff Explorer actions on a folder: rename and delete (cascade). */
export function FolderActions({ folderId, name }: { folderId: string; name: string }) {
  const router = useRouter();
  const toast = useToast();
  const [busy, setBusy] = useState(false);

  async function rename() {
    const next = window.prompt('Novo nome da pasta:', name);
    if (next === null || !next.trim() || next.trim() === name) return;
    setBusy(true);
    const response = await fetch(`/api/portal/folders/${folderId}/rename`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: next.trim() }),
    });
    setBusy(false);
    if (response.ok) {
      toast.success('Pasta renomeada.');
      router.refresh();
    } else {
      const payload = await response.json().catch(() => ({}));
      toast.error(payload?.message ?? 'Não foi possível renomear.');
    }
  }

  async function remove() {
    if (
      !window.confirm(
        `Eliminar a pasta "${name}" e TODO o seu conteúdo (documentos e subpastas)? Esta ação não pode ser anulada.`,
      )
    ) {
      return;
    }
    setBusy(true);
    const response = await fetch(`/api/portal/folders/${folderId}/delete`, { method: 'POST' });
    setBusy(false);
    if (response.ok) {
      toast.success('Pasta eliminada.');
      router.refresh();
    } else {
      const payload = await response.json().catch(() => ({}));
      toast.error(payload?.message ?? 'Não foi possível eliminar.');
    }
  }

  return (
    <span className="flex items-center gap-1">
      <Button variant="secondary" size="sm" onClick={rename} disabled={busy} aria-label="Renomear pasta">
        {busy ? <Loader2 className="size-4 animate-spin" /> : <Pencil className="size-4" />}
      </Button>
      <Button variant="danger" size="sm" onClick={remove} disabled={busy} aria-label="Eliminar pasta">
        <Trash2 className="size-4" />
      </Button>
    </span>
  );
}
