'use client';

import { Download, Loader2 } from 'lucide-react';
import { useState } from 'react';

import { Button } from '@/components/ui';

/** Pulls the filename out of a Content-Disposition header, falling back to a default. */
function filenameFrom(disposition: string | null): string {
  if (!disposition) return 'documento';
  const utf8 = /filename\*=UTF-8''([^;]+)/i.exec(disposition);
  if (utf8) return decodeURIComponent(utf8[1]);
  const plain = /filename="?([^";]+)"?/i.exec(disposition);
  return plain ? plain[1] : 'documento';
}

/**
 * Streams the document from the authenticated backend and saves it.
 *
 * The file is piped through the API (never a public storage URL), and each
 * download is authorised and audited server-side.
 */
export function DownloadButton({ documentId }: { documentId: string }) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function download() {
    setBusy(true);
    setError(null);
    try {
      const response = await fetch(`/api/portal/documents/${documentId}/file`);
      if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        setError(payload.message ?? 'Download não autorizado.');
        return;
      }
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement('a');
      anchor.href = url;
      anchor.download = filenameFrom(response.headers.get('content-disposition'));
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      URL.revokeObjectURL(url);
    } catch {
      setError('Não foi possível descarregar.');
    } finally {
      setBusy(false);
    }
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
