'use client';

import { Loader2, Upload } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useRef, useState } from 'react';

import { Alert, Button, Card, CardHeader, Field, Textarea } from '@/components/ui';
import { formatBytes } from '@/lib/utils/format';

type Upload = { name: string; size: number; state: 'uploading' | 'done' | 'error'; message?: string };

/**
 * Drag-and-drop uploader. A file is only reported as received once the backend
 * confirms it; availability still depends on the antivirus scan.
 */
export function DocumentUploader({
  clientId,
  protocolId,
  folderId,
  requirementId,
  zipOnly = false,
}: {
  clientId?: string;
  protocolId?: string;
  folderId?: string;
  requirementId?: string;
  /** Clients deliver one ZIP per submission; the backend enforces the same rule. */
  zipOnly?: boolean;
}) {
  const router = useRouter();
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [uploads, setUploads] = useState<Upload[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [note, setNote] = useState('');

  async function send(files: FileList | null) {
    if (!files?.length) return;
    setError(null);

    for (const file of Array.from(files)) {
      setUploads((current) => [...current, { name: file.name, size: file.size, state: 'uploading' }]);
      const body = new FormData();
      body.set('file', file);
      if (note.trim()) body.set('note', note.trim());
      if (protocolId) body.set('protocol', protocolId);
      else if (clientId) body.set('client', clientId);
      if (folderId) body.set('folder', folderId);
      if (requirementId) body.set('requirement', requirementId);

      const response = await fetch('/api/portal/documents/upload', { method: 'POST', body });
      const payload = await response.json().catch(() => ({}));
      const ok = response.ok && payload.success;

      setUploads((current) =>
        current.map((item) =>
          item.name === file.name && item.state === 'uploading'
            ? { ...item, state: ok ? 'done' : 'error', message: ok ? undefined : payload.message }
            : item,
        ),
      );
      if (!ok) setError(payload.message ?? 'O envio falhou.');
    }
    setNote('');
    router.refresh();
  }

  return (
    <Card>
      <CardHeader
        title="Enviar documentos"
        description={
          zipOnly
            ? 'Envie um único ficheiro .zip com os documentos do período.'
            : 'PDF, XML, CSV, imagens, Office e ZIP.'
        }
      />
      <div className="space-y-3 px-5 py-4">
        {error ? <Alert>{error}</Alert> : null}

        <Field label="Observação (opcional)">
          <Textarea
            value={note}
            onChange={(event) => setNote(event.target.value)}
            placeholder="Uma nota para acompanhar este envio."
            rows={2}
          />
        </Field>

        <div
          onDragOver={(event) => {
            event.preventDefault();
            setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={(event) => {
            event.preventDefault();
            setDragging(false);
            void send(event.dataTransfer.files);
          }}
          className={`rounded-xl border-2 border-dashed px-6 py-8 text-center transition-colors ${
            dragging ? 'border-zinc-900 bg-mist/30' : 'border-mist'
          }`}
        >
          <Upload className="mx-auto size-5 text-navy/40" aria-hidden />
          <p className="text-navy/70 mt-2 text-sm">
            {zipOnly ? 'Arraste o ficheiro .zip para aqui' : 'Arraste os ficheiros para aqui'}
          </p>
          <Button type="button" variant="secondary" size="sm" className="mt-3" onClick={() => inputRef.current?.click()}>
            {zipOnly ? 'Escolher ficheiro .zip' : 'Escolher ficheiros'}
          </Button>
          <input
            ref={inputRef}
            type="file"
            multiple={!zipOnly}
            accept={zipOnly ? '.zip,application/zip' : undefined}
            className="hidden"
            onChange={(event) => void send(event.target.files)}
          />
        </div>

        {uploads.length ? (
          <ul className="space-y-1.5">
            {uploads.map((item, index) => (
              <li key={`${item.name}-${index}`} className="flex items-center justify-between gap-3 text-sm">
                <span className="truncate text-navy/80">{item.name}</span>
                <span className="flex items-center gap-2 whitespace-nowrap text-navy/55">
                  {formatBytes(item.size)}
                  {item.state === 'uploading' ? <Loader2 className="size-4 animate-spin" aria-label="A enviar" /> : null}
                  {item.state === 'done' ? <span className="text-emerald-600">recebido</span> : null}
                  {item.state === 'error' ? <span className="text-red-600">falhou</span> : null}
                </span>
              </li>
            ))}
          </ul>
        ) : null}
      </div>
    </Card>
  );
}
