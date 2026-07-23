'use client';

import { FolderPlus, Loader2 } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useState } from 'react';

import { Button, Input } from '@/components/ui';

/** Creates a subfolder in the folder currently open. Staff only. */
export function NewFolderForm({ clientId, parentId }: { clientId: string; parentId: string | null }) {
  const router = useRouter();
  const [name, setName] = useState('');
  const [internal, setInternal] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    if (!name.trim()) return;
    setBusy(true);
    setError(null);
    const response = await fetch('/api/portal/folders', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        client: clientId,
        name,
        parent: parentId,
        visibility: internal ? 'staff_only' : 'client_and_staff',
      }),
    });
    const payload = await response.json().catch(() => ({}));
    setBusy(false);
    if (!response.ok || !payload.success) {
      setError(payload.message ?? 'Não foi possível criar a pasta.');
      return;
    }
    setName('');
    router.refresh();
  }

  return (
    <form onSubmit={submit} className="flex items-center gap-2">
      <Input
        value={name}
        onChange={(event) => setName(event.target.value)}
        placeholder="Nova pasta"
        aria-label="Nome da nova pasta"
        className="h-9 w-44"
      />
      <label className="text-navy/70 flex items-center gap-1.5 text-xs whitespace-nowrap">
        <input type="checkbox" checked={internal} onChange={(event) => setInternal(event.target.checked)} />
        Interna
      </label>
      <Button type="submit" variant="secondary" size="sm" disabled={busy || !name.trim()}>
        {busy ? <Loader2 className="size-4 animate-spin" /> : <FolderPlus className="size-4" aria-hidden />}
        Criar
      </Button>
      {error ? <span className="text-xs text-red-600">{error}</span> : null}
    </form>
  );
}
