'use client';

import { zodResolver } from '@hookform/resolvers/zod';
import { Loader2 } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useState } from 'react';
import { useForm } from 'react-hook-form';

import { LogoutButton } from '@/components/logout-button';
import { Alert, Badge, Button, Card, CardHeader, Field, Input, PageHeader } from '@/components/ui';
import { formatDateTime } from '@/lib/utils/format';
import { changePasswordSchema, type ChangePasswordInput } from '@/lib/validation/schemas';
import type { Session, User } from '@/types';

export function SecurityPanel({ user, sessions }: { user: User; sessions: Session[] }) {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const form = useForm<ChangePasswordInput>({ resolver: zodResolver(changePasswordSchema) });

  async function changePassword(values: ChangePasswordInput) {
    setError(null);
    setNotice(null);
    const response = await fetch('/api/auth/password', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'change', ...values }),
    });
    const payload = await response.json();
    if (!response.ok || !payload.success) {
      setError(payload.message ?? 'Não foi possível alterar a palavra-passe.');
      return;
    }
    setNotice('Palavra-passe alterada. Todas as sessões foram terminadas.');
    form.reset();
    setTimeout(() => {
      router.replace('/entrar');
      router.refresh();
    }, 2000);
  }

  async function revoke(sessionId: string) {
    const response = await fetch(`/api/auth/sessions/${sessionId}/revoke`, { method: 'POST' });
    if (response.ok) router.refresh();
  }

  const active = sessions.filter((session) => session.status === 'active');

  return (
    <>
      <PageHeader title="Segurança" description={user.email} />

      <Card>
        <CardHeader
          title="Sessões ativas"
          description={`${active.length} sessão(ões) em curso.`}
          action={<LogoutButton all label="Terminar todas" />}
        />
        <ul className="divide-y divide-mist/70">
          {sessions.slice(0, 15).map((session) => (
            <li key={session.id} className="flex flex-wrap items-center justify-between gap-3 px-5 py-3">
              <div>
                <p className="text-sm font-medium text-navy">{session.device || 'Dispositivo desconhecido'}</p>
                <p className="mt-0.5 text-xs text-navy/55">
                  {[session.ip_address, session.country_code, `última atividade ${formatDateTime(session.last_activity_at)}`]
                    .filter(Boolean)
                    .join(' · ')}
                </p>
              </div>
              <div className="flex items-center gap-2">
                <Badge tone={session.status === 'active' ? 'success' : 'neutral'}>{session.status}</Badge>
                {session.status === 'active' ? (
                  <Button variant="danger" size="sm" onClick={() => revoke(session.id)}>
                    Revogar
                  </Button>
                ) : null}
              </div>
            </li>
          ))}
        </ul>
      </Card>

      <Card>
        <CardHeader title="Alterar palavra-passe" description="Ao alterar, todas as sessões são terminadas." />
        <form onSubmit={form.handleSubmit(changePassword)} className="max-w-md space-y-4 px-5 py-4">
          {error ? <Alert>{error}</Alert> : null}
          {notice ? <Alert tone="success">{notice}</Alert> : null}
          <Field label="Palavra-passe atual" error={form.formState.errors.current_password?.message}>
            <Input {...form.register('current_password')} type="password" autoComplete="current-password" />
          </Field>
          <Field label="Nova palavra-passe" error={form.formState.errors.password?.message}>
            <Input {...form.register('password')} type="password" autoComplete="new-password" />
          </Field>
          <Field label="Repetir nova palavra-passe" error={form.formState.errors.password2?.message}>
            <Input {...form.register('password2')} type="password" autoComplete="new-password" />
          </Field>
          <Button type="submit" disabled={form.formState.isSubmitting}>
            {form.formState.isSubmitting ? <Loader2 className="size-4 animate-spin" /> : null}
            Alterar palavra-passe
          </Button>
        </form>
      </Card>
    </>
  );
}
