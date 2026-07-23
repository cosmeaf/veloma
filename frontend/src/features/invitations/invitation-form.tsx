'use client';

import { Loader2, Send } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useState } from 'react';

import { Alert, Button, Card, CardHeader, Field, Input, Select } from '@/components/ui';
import { MEMBER_ROLES } from '@/lib/utils/format';

export function InvitationForm({ clientId, clientName }: { clientId: string; clientName: string }) {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [role, setRole] = useState('employee');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    setNotice(null);

    const response = await fetch('/api/portal/invitations', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ client: clientId, email, role }),
    });
    const payload = await response.json().catch(() => ({}));
    setBusy(false);

    if (!response.ok || !payload.success) {
      setError(payload.message ?? 'Não foi possível enviar o convite.');
      return;
    }
    setNotice(`Convite enviado para ${email}.`);
    setEmail('');
    router.refresh();
  }

  return (
    <Card>
      <CardHeader title="Convidar membro" description={`O convite dá acesso a ${clientName}.`} />
      <form onSubmit={submit} className="space-y-4 px-5 py-4">
        {error ? <Alert>{error}</Alert> : null}
        {notice ? <Alert tone="success">{notice}</Alert> : null}
        <Field label="E-mail">
          <Input
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            placeholder="nome@empresa.pt"
            required
          />
        </Field>
        <Field label="Função">
          <Select value={role} onChange={(event) => setRole(event.target.value)}>
            {Object.entries(MEMBER_ROLES).map(([value, text]) => (
              <option key={value} value={value}>
                {text}
              </option>
            ))}
          </Select>
        </Field>
        <Button type="submit" disabled={busy || !email}>
          {busy ? <Loader2 className="size-4 animate-spin" /> : <Send className="size-4" aria-hidden />}
          Enviar convite
        </Button>
      </form>
    </Card>
  );
}
