'use client';

import { Loader2, Plus } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useState } from 'react';

import { useToast } from '@/components/toast';
import { Alert, Button, Card, CardHeader, Field, Input, Select, Textarea } from '@/components/ui';
import { formatDateTime } from '@/lib/utils/format';
import type { Protocol, ProtocolSubject } from '@/types';

/**
 * Client self-service: pick a subject and open a request. The subject's SLA
 * sets the response deadline, shown back on confirmation.
 */
export function OpenRequestPanel() {
  const router = useRouter();
  const toast = useToast();
  const [open, setOpen] = useState(false);
  const [subjects, setSubjects] = useState<ProtocolSubject[] | null>(null);
  const [subjectId, setSubjectId] = useState('');
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [created, setCreated] = useState<Protocol | null>(null);

  async function reveal() {
    setOpen(true);
    if (subjects) return;
    const response = await fetch('/api/portal/subjects');
    const payload = await response.json();
    const list: ProtocolSubject[] = payload?.data?.subjects ?? [];
    setSubjects(list);
    if (list.length) setSubjectId(list[0].id);
  }

  const selected = subjects?.find((s) => s.id === subjectId) ?? null;

  async function submit() {
    if (!subjectId) return;
    setSubmitting(true);
    setError(null);
    const response = await fetch('/api/portal/requests', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ subject: subjectId, title, description }),
    });
    const payload = await response.json();
    setSubmitting(false);
    if (!response.ok || !payload?.data?.protocol) {
      setError(payload?.message ?? 'Não foi possível abrir o pedido.');
      return;
    }
    const protocol: Protocol = payload.data.protocol;
    setCreated(protocol);
    setTitle('');
    setDescription('');
    toast.success(`Pedido ${protocol.number} aberto.`);
    router.refresh();
  }

  if (created) {
    return (
      <Card className="border-emerald-200 bg-emerald-50/60">
        <div className="space-y-3 px-5 py-4">
          <p className="text-navy text-sm font-medium">Pedido {created.number} aberto.</p>
          <p className="text-navy/70 text-sm">
            Recebemos o seu pedido. A Veloma responde
            {created.response_due_at ? ` até ${formatDateTime(created.response_due_at)}` : ' dentro do prazo indicado'}
            {created.sla_hours ? ` (${created.sla_hours}h).` : '.'}
          </p>
          <div className="flex flex-wrap gap-2">
            <Button onClick={() => router.push(`/dashboard/protocolos/${created.id}`)}>Enviar documentos</Button>
            <Button variant="secondary" onClick={() => setCreated(null)}>
              Abrir outro pedido
            </Button>
          </div>
        </div>
      </Card>
    );
  }

  if (!open) {
    return (
      <Button onClick={reveal}>
        <Plus className="size-4" />
        Abrir pedido
      </Button>
    );
  }

  return (
    <Card>
      <CardHeader title="Abrir pedido" description="Escolha o assunto; indicamos o prazo de resposta." />
      <div className="space-y-4 px-5 py-4">
        {error ? <Alert>{error}</Alert> : null}
        <Field label="Assunto">
          <Select value={subjectId} onChange={(event) => setSubjectId(event.target.value)}>
            {(subjects ?? []).map((subject) => (
              <option key={subject.id} value={subject.id}>
                {subject.name} — resposta até {subject.sla_hours}h
              </option>
            ))}
          </Select>
        </Field>
        {selected?.description ? <p className="text-navy/60 -mt-2 text-xs">{selected.description}</p> : null}
        <Field label="Título (opcional)" hint="Se deixar em branco, usamos o nome do assunto.">
          <Input value={title} onChange={(event) => setTitle(event.target.value)} placeholder={selected?.name ?? ''} />
        </Field>
        <Field label="Descrição (opcional)">
          <Textarea
            value={description}
            onChange={(event) => setDescription(event.target.value)}
            placeholder="Detalhes que ajudem a nossa equipa."
          />
        </Field>
        <div className="flex flex-wrap gap-2">
          <Button onClick={submit} disabled={submitting || !subjectId}>
            {submitting ? <Loader2 className="size-4 animate-spin" /> : null}
            Abrir pedido
          </Button>
          <Button variant="secondary" onClick={() => setOpen(false)}>
            Cancelar
          </Button>
        </div>
      </div>
    </Card>
  );
}
