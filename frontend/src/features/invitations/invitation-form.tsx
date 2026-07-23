'use client';

import { Loader2, Send } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useState } from 'react';

import { Alert, Button, Card, CardHeader, Field, Input, Select } from '@/components/ui';
import { MEMBER_ROLES } from '@/lib/utils/format';

type ClientOption = { id: string; legal_name: string };

/**
 * Sends an invitation. When `clients` is provided the office picks the target
 * company here (invitations tab); on a client's own page the client is fixed.
 */
export function InvitationForm({
  clientId,
  clientName,
  clients,
}: {
  clientId?: string;
  clientName?: string;
  clients?: ClientOption[];
}) {
  const router = useRouter();
  const [client, setClient] = useState(clientId ?? clients?.[0]?.id ?? '');
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
      body: JSON.stringify({ client, email, role }),
    });
    const payload = await response.json().catch(() => ({}));
    setBusy(false);

    if (!response.ok || !payload.success) {
      setError(payload.message ?? 'Não foi possível enviar o convite.');
      return;
    }
    setNotice(`Convite enviado por e-mail para ${email}. O acesso só é criado através desse link.`);
    setEmail('');
    router.refresh();
  }

  const description = clientName
    ? `Enviado por e-mail. Dá acesso a ${clientName}.`
    : 'Enviado por e-mail. Escolha a empresa e o endereço a convidar.';

  return (
    <Card>
      <CardHeader title="Convidar membro" description={description} />
      <form onSubmit={submit} className="space-y-4 px-5 py-4">
        {error ? <Alert>{error}</Alert> : null}
        {notice ? <Alert tone="success">{notice}</Alert> : null}

        {clients ? (
          <Field label="Empresa">
            <Select value={client} onChange={(event) => setClient(event.target.value)} required>
              <option value="" disabled>
                Escolha a empresa…
              </option>
              {clients.map((option) => (
                <option key={option.id} value={option.id}>
                  {option.legal_name}
                </option>
              ))}
            </Select>
          </Field>
        ) : null}

        <div className="grid gap-4 sm:grid-cols-2">
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
        </div>

        <Button type="submit" disabled={busy || !email || !client}>
          {busy ? <Loader2 className="size-4 animate-spin" /> : <Send className="size-4" aria-hidden />}
          Enviar convite
        </Button>
      </form>
    </Card>
  );
}
