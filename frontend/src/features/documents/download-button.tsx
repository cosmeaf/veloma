'use client';

import { Download, Loader2 } from 'lucide-react';
import { useState } from 'react';

import { Button } from '@/components/ui';

/**
 * Asks the backend for a short-lived signed URL and opens it.
 *
 * The URL is never stored: each download is authorised and audited server-side.
 */
export function DownloadButton({ documentId }: { documentId: string }) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function download() {
    setBusy(true);
    setError(null);
    const response = await fetch(`/api/portal/documents/${documentId}/download`, { method: 'POST' });
    const payload = await response.json().catch(() => ({}));
    setBusy(false);
    if (!response.ok || !payload.success) {
      setError(payload.message ?? 'Download não autorizado.');
      return;
    }
    window.open(payload.data.url, '_blank', 'noopener,noreferrer');
  }

  return (
    <div className="flex items-center gap-2">
      {error ? <span className="text-xs text-red-600">{error}</span> : null}
      <Button variant="secondary" size="sm" onClick={download} disabled={busy}>
        {busy ? <Loader2 className="size-4 animate-spin" aria-hidden /> : <Download className="size-4" aria-hidden />}
        Descarregar
      </Button>
    </div>
  );
}
