'use client';

import { zodResolver } from '@hookform/resolvers/zod';
import { Loader2 } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useState } from 'react';
import { useForm } from 'react-hook-form';

import { Alert, Button, Field, Input } from '@/components/ui';
import { firstAccessSchema, type FirstAccessInput } from '@/lib/validation/schemas';

/**
 * Replaces the shared credentials of a seeded account.
 *
 * The backend revokes every session afterwards, so the holder signs in again
 * with the new e-mail and password.
 */
export function FirstAccessForm({ currentEmail }: { currentEmail: string }) {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState(false);

  const form = useForm<FirstAccessInput>({
    resolver: zodResolver(firstAccessSchema),
    defaultValues: { email: currentEmail },
  });

  async function onSubmit(values: FirstAccessInput) {
    setError(null);
    const response = await fetch('/api/auth/first-access', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(values),
    });
    const payload = await response.json();
    if (!response.ok || !payload.success) {
      setError(payload.message ?? 'Não foi possível concluir o primeiro acesso.');
      return;
    }
    setDone(true);
    setTimeout(() => {
      router.replace('/entrar');
      router.refresh();
    }, 2500);
  }

  if (done) {
    return <Alert tone="success">Credenciais atualizadas. Entre novamente com o novo e-mail e palavra-passe.</Alert>;
  }

  return (
    <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
      {error ? <Alert>{error}</Alert> : null}

      <Field
        label="O seu e-mail"
        error={form.formState.errors.email?.message}
        hint="Pode manter o e-mail do departamento ou usar o seu."
      >
        <Input {...form.register('email')} type="email" autoComplete="email" autoFocus />
      </Field>
      <Field
        label="Nova palavra-passe"
        error={form.formState.errors.password?.message}
        hint="Tem de ser diferente da palavra-passe temporária."
      >
        <Input {...form.register('password')} type="password" autoComplete="new-password" />
      </Field>
      <Field label="Repetir palavra-passe" error={form.formState.errors.password2?.message}>
        <Input {...form.register('password2')} type="password" autoComplete="new-password" />
      </Field>

      <Button type="submit" className="w-full" disabled={form.formState.isSubmitting}>
        {form.formState.isSubmitting ? <Loader2 className="size-4 animate-spin" /> : null}
        Concluir primeiro acesso
      </Button>
    </form>
  );
}
