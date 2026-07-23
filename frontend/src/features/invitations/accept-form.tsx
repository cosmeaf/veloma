'use client';

import { zodResolver } from '@hookform/resolvers/zod';
import { Loader2 } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useState } from 'react';
import { useForm } from 'react-hook-form';

import { Alert, Button, Field, Input } from '@/components/ui';
import { acceptInvitationSchema, type AcceptInvitationInput } from '@/lib/validation/schemas';

export function AcceptInvitationForm({
  token,
  email,
  clientName,
}: {
  token: string;
  email: string;
  clientName: string;
}) {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState(false);

  const form = useForm<AcceptInvitationInput>({
    resolver: zodResolver(acceptInvitationSchema),
    defaultValues: { first_name: '', last_name: '', phone: '', position: '' },
  });

  async function onSubmit(values: AcceptInvitationInput) {
    setError(null);
    const response = await fetch('/api/invitations/accept', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token, ...values }),
    });
    const payload = await response.json();
    if (!response.ok || !payload.success) {
      setError(payload.message ?? 'Não foi possível concluir o registo.');
      return;
    }
    setDone(true);
    setTimeout(() => router.replace('/entrar'), 2500);
  }

  if (done) {
    return <Alert tone="success">Conta criada. Vai ser encaminhado para a página de entrada.</Alert>;
  }

  return (
    <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
      <Alert tone="info">
        Convite para <strong>{clientName}</strong>.
      </Alert>
      {error ? <Alert>{error}</Alert> : null}

      <Field label="E-mail">
        <Input value={email} readOnly disabled />
      </Field>

      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Primeiro nome" error={form.formState.errors.first_name?.message}>
          <Input {...form.register('first_name')} autoComplete="given-name" autoFocus />
        </Field>
        <Field label="Apelido" error={form.formState.errors.last_name?.message}>
          <Input {...form.register('last_name')} autoComplete="family-name" />
        </Field>
        <Field label="Telefone" error={form.formState.errors.phone?.message}>
          <Input {...form.register('phone')} autoComplete="tel" />
        </Field>
        <Field label="Cargo ou função" error={form.formState.errors.position?.message}>
          <Input {...form.register('position')} />
        </Field>
        <Field label="Palavra-passe" error={form.formState.errors.password?.message}>
          <Input {...form.register('password')} type="password" autoComplete="new-password" />
        </Field>
        <Field label="Repetir palavra-passe" error={form.formState.errors.password2?.message}>
          <Input {...form.register('password2')} type="password" autoComplete="new-password" />
        </Field>
      </div>

      <div className="space-y-2">
        <label className="flex items-start gap-2 text-sm text-navy/80">
          <input type="checkbox" {...form.register('accept_terms')} className="mt-0.5" />
          <span>
            Aceito os{' '}
            <a href="/termos" target="_blank" rel="noreferrer noopener" className="font-medium text-navy underline">
              Termos e Condições
            </a>
            .
          </span>
        </label>
        {form.formState.errors.accept_terms ? (
          <p className="text-xs font-medium text-red-600">{form.formState.errors.accept_terms.message}</p>
        ) : null}
        <label className="flex items-start gap-2 text-sm text-navy/80">
          <input type="checkbox" {...form.register('accept_privacy_policy')} className="mt-0.5" />
          <span>
            Aceito a{' '}
            <a href="/privacidade" target="_blank" rel="noreferrer noopener" className="font-medium text-navy underline">
              Política de Privacidade
            </a>
            .
          </span>
        </label>
        {form.formState.errors.accept_privacy_policy ? (
          <p className="text-xs font-medium text-red-600">{form.formState.errors.accept_privacy_policy.message}</p>
        ) : null}
      </div>

      <Button type="submit" className="w-full" disabled={form.formState.isSubmitting}>
        {form.formState.isSubmitting ? <Loader2 className="size-4 animate-spin" /> : null}
        Criar conta
      </Button>
    </form>
  );
}
