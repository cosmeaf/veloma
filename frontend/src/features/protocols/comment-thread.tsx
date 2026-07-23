'use client';

import { Loader2, Lock } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useState } from 'react';

import { Alert, Badge, Button, Card, CardHeader, Textarea } from '@/components/ui';
import { formatDateTime } from '@/lib/utils/format';
import type { Comment } from '@/types';

export function CommentThread({
  protocolId,
  comments,
  canComment,
  canWriteInternal,
}: {
  protocolId: string;
  comments: Comment[];
  canComment: boolean;
  canWriteInternal: boolean;
}) {
  const router = useRouter();
  const [message, setMessage] = useState('');
  const [internal, setInternal] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    if (!message.trim()) return;
    setBusy(true);
    setError(null);
    const response = await fetch(`/api/portal/protocols/${protocolId}/comments`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, visibility: internal ? 'internal' : 'public' }),
    });
    const payload = await response.json();
    setBusy(false);
    if (!response.ok || !payload.success) {
      setError(payload.message ?? 'Não foi possível enviar a mensagem.');
      return;
    }
    setMessage('');
    router.refresh();
  }

  return (
    <Card>
      <CardHeader title="Mensagens" description="Comunicação sobre este protocolo." />
      <ul className="divide-y divide-mist/70">
        {comments.length === 0 ? (
          <li className="px-5 py-8 text-center text-sm text-navy/55">Ainda não há mensagens.</li>
        ) : (
          comments.map((comment) => (
            <li key={comment.id} className="px-5 py-4">
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-navy">{comment.author_name_snapshot || 'Veloma'}</span>
                {comment.visibility === 'internal' ? (
                  <Badge tone="warning">
                    <Lock className="mr-1 size-3" aria-hidden />
                    Nota interna
                  </Badge>
                ) : null}
                <time className="ml-auto text-xs text-navy/40">{formatDateTime(comment.created_at)}</time>
              </div>
              <p className="mt-1.5 text-sm whitespace-pre-wrap text-navy/80">{comment.message}</p>
            </li>
          ))
        )}
      </ul>

      {canComment ? (
        <form onSubmit={submit} className="space-y-3 border-t border-mist px-5 py-4">
          {error ? <Alert>{error}</Alert> : null}
          <Textarea
            value={message}
            onChange={(event) => setMessage(event.target.value)}
            placeholder="Escreva uma mensagem…"
            aria-label="Mensagem"
          />
          <div className="flex items-center justify-between gap-3">
            {canWriteInternal ? (
              <label className="flex items-center gap-2 text-sm text-navy/70">
                <input type="checkbox" checked={internal} onChange={(event) => setInternal(event.target.checked)} />
                Nota interna (não visível ao cliente)
              </label>
            ) : (
              <span />
            )}
            <Button type="submit" size="sm" disabled={busy || !message.trim()}>
              {busy ? <Loader2 className="size-4 animate-spin" /> : null}
              Enviar
            </Button>
          </div>
        </form>
      ) : null}
    </Card>
  );
}
