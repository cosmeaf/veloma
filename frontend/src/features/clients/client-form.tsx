'use client';

import { zodResolver } from '@hookform/resolvers/zod';
import { Loader2, Plus, X } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useState } from 'react';
import { useForm } from 'react-hook-form';

import { Alert, Button, Field, Input, Select } from '@/components/ui';
import { MEMBER_ROLES } from '@/lib/utils/format';
import { clientSchema, type ClientInput } from '@/lib/validation/schemas';

const ENTITY_TYPES = [
  ['quotas', 'Sociedade por quotas'],
  ['unipessoal', 'Sociedade unipessoal'],
  ['eni', 'Empresário em nome individual'],
  ['independent', 'Trabalhador independente'],
  ['association', 'Associação'],
  ['foundation', 'Fundação'],
  ['condominium', 'Condomínio'],
  ['other', 'Outro'],
] as const;

/** Collapsible "new client" panel shown above the client list. */
export function NewClientForm() {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);
  // Since clients only ever enter by invitation, offer to send one right away.
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState('owner');

  const form = useForm<ClientInput>({
    resolver: zodResolver(clientSchema),
    defaultValues: { entity_type: 'quotas' },
  });

  async function onSubmit(values: ClientInput) {
    setError(null);
    const response = await fetch('/api/portal/clients', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(values),
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok || !payload.success) {
      setError(payload.message ?? 'Não foi possível criar o cliente.');
      return;
    }
    const id = payload.data?.client?.id as string | undefined;

    // Optional invitation in the same step.
    if (id && inviteEmail.trim()) {
      const invite = await fetch('/api/portal/invitations', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ client: id, email: inviteEmail.trim(), role: inviteRole }),
      });
      if (!invite.ok) {
        // The client was created; surface the invite problem but continue.
        const invitePayload = await invite.json().catch(() => ({}));
        setError(`Cliente criado, mas o convite falhou: ${invitePayload.message ?? 'erro'}`);
        if (id) router.push(`/staff/clientes/${id}`);
        return;
      }
    }

    form.reset();
    setInviteEmail('');
    setOpen(false);
    if (id) router.push(`/staff/clientes/${id}`);
    else router.refresh();
  }

  if (!open) {
    return (
      <div className="flex justify-end">
        <Button onClick={() => setOpen(true)}>
          <Plus className="size-4" aria-hidden />
          Novo cliente
        </Button>
      </div>
    );
  }

  return (
    <div className="border-mist rounded-xl border bg-white p-5">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-navy text-sm font-semibold">Novo cliente</h2>
        <button type="button" onClick={() => setOpen(false)} aria-label="Fechar" className="text-navy/40 hover:text-navy">
          <X className="size-4" />
        </button>
      </div>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
        {error ? <Alert>{error}</Alert> : null}
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Denominação social" error={form.formState.errors.legal_name?.message}>
            <Input {...form.register('legal_name')} autoFocus />
          </Field>
          <Field label="Nome comercial" error={form.formState.errors.commercial_name?.message}>
            <Input {...form.register('commercial_name')} />
          </Field>
          <Field label="NIF" error={form.formState.errors.nif?.message}>
            <Input {...form.register('nif')} inputMode="numeric" placeholder="9 dígitos" />
          </Field>
          <Field label="Tipo de entidade" error={form.formState.errors.entity_type?.message}>
            <Select {...form.register('entity_type')}>
              {ENTITY_TYPES.map(([value, labelText]) => (
                <option key={value} value={value}>
                  {labelText}
                </option>
              ))}
            </Select>
          </Field>
          <Field label="E-mail" error={form.formState.errors.email?.message}>
            <Input {...form.register('email')} type="email" />
          </Field>
          <Field label="Telefone" error={form.formState.errors.phone?.message}>
            <Input {...form.register('phone')} />
          </Field>
          <Field label="Cidade" error={form.formState.errors.city?.message}>
            <Input {...form.register('city')} />
          </Field>
        </div>

        <div className="border-mist border-t pt-4">
          <p className="text-navy text-sm font-medium">Convidar o cliente (opcional)</p>
          <p className="text-navy/55 mt-0.5 mb-3 text-xs">
            O cliente entra apenas por convite. Envie já um por e-mail, ou deixe em branco e convide depois.
          </p>
          <div className="grid gap-4 sm:grid-cols-2">
            <Field label="E-mail do responsável">
              <Input
                type="email"
                value={inviteEmail}
                onChange={(event) => setInviteEmail(event.target.value)}
                placeholder="nome@empresa.pt"
              />
            </Field>
            <Field label="Função">
              <Select value={inviteRole} onChange={(event) => setInviteRole(event.target.value)}>
                {Object.entries(MEMBER_ROLES).map(([value, text]) => (
                  <option key={value} value={value}>
                    {text}
                  </option>
                ))}
              </Select>
            </Field>
          </div>
        </div>

        <div className="flex gap-2">
          <Button type="submit" disabled={form.formState.isSubmitting}>
            {form.formState.isSubmitting ? <Loader2 className="size-4 animate-spin" /> : null}
            {inviteEmail.trim() ? 'Criar e convidar' : 'Criar cliente'}
          </Button>
          <Button type="button" variant="secondary" onClick={() => setOpen(false)}>
            Cancelar
          </Button>
        </div>
      </form>
    </div>
  );
}
