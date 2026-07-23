'use client';

import { zodResolver } from '@hookform/resolvers/zod';
import { Loader2, MonitorSmartphone, ShieldCheck } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useState } from 'react';
import { useForm } from 'react-hook-form';

import { LogoutButton } from '@/components/logout-button';
import { useToast } from '@/components/toast';
import { Alert, Badge, Button, Card, CardHeader, EmptyState, Field, Input, PageHeader } from '@/components/ui';
import { formatDateTime } from '@/lib/utils/format';
import { changePasswordSchema, type ChangePasswordInput } from '@/lib/validation/schemas';
import type { AccessEvent, Session, User } from '@/types';

const EVENT_LABELS: Record<string, string> = {
  login: 'Início de sessão',
  login_otp: 'Início de sessão (2FA)',
  token_refresh: 'Sessão renovada',
  first_access: 'Primeiro acesso',
};

const STATUS_TONE = { success: 'success', failed: 'danger', blocked: 'danger' } as const;

export function SecurityPanel({
  user,
  sessions,
  history,
}: {
  user: User;
  sessions: Session[];
  history: AccessEvent[];
}) {
  const router = useRouter();
  const toast = useToast();
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [twoFactor, setTwoFactor] = useState(Boolean(user.two_factor_email));
  const [savingTwoFactor, setSavingTwoFactor] = useState(false);

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

  async function toggleTwoFactor(next: boolean) {
    setSavingTwoFactor(true);
    const response = await fetch('/api/auth/two-factor', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ enabled: next }),
    });
    setSavingTwoFactor(false);
    if (response.ok) {
      setTwoFactor(next);
      toast.success(
        next
          ? 'Verificação em duas etapas ativada. A partir de agora recebe um código por e-mail ao entrar.'
          : 'Verificação em duas etapas desativada.',
      );
      router.refresh();
    } else {
      toast.error('Não foi possível atualizar a verificação em duas etapas.');
    }
  }

  async function revoke(sessionId: string) {
    const response = await fetch(`/api/auth/sessions/${sessionId}/revoke`, { method: 'POST' });
    if (response.ok) {
      toast.success('Sessão revogada.');
      router.refresh();
    } else {
      toast.error('Não foi possível revogar a sessão.');
    }
  }

  const active = sessions.filter((session) => session.status === 'active');

  return (
    <>
      <PageHeader title="Segurança" description={user.email} />

      {/* Two columns: 2FA and password change side by side. */}
      <div className="grid items-start gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader
            title="Verificação em duas etapas"
            description="Um código enviado por e-mail a cada início de sessão."
          />
          <div className="flex items-center justify-between gap-4 px-5 py-4">
            <div className="flex items-start gap-3">
              <span className="bg-navy inline-flex size-9 items-center justify-center rounded-lg">
                <ShieldCheck className="text-gold size-4.5" aria-hidden />
              </span>
              <div>
                <p className="text-navy text-sm font-medium">
                  {twoFactor ? 'Ativa' : 'Desativada'}
                </p>
                <p className="text-navy/55 mt-0.5 text-xs">
                  {twoFactor
                    ? 'Ao entrar, pedimos o código enviado para o seu e-mail.'
                    : 'Reforça a proteção da sua conta com um segundo passo.'}
                </p>
              </div>
            </div>
            <Button
              variant={twoFactor ? 'secondary' : 'primary'}
              size="sm"
              disabled={savingTwoFactor}
              onClick={() => toggleTwoFactor(!twoFactor)}
            >
              {savingTwoFactor ? <Loader2 className="size-4 animate-spin" /> : null}
              {twoFactor ? 'Desativar' : 'Ativar'}
            </Button>
          </div>
        </Card>

        <Card>
          <CardHeader title="Alterar palavra-passe" description="Ao alterar, todas as sessões são terminadas." />
          <form onSubmit={form.handleSubmit(changePassword)} className="space-y-4 px-5 py-4">
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
      </div>

      <Card>
        <CardHeader
          title="Sessões ativas"
          description={`${active.length} sessão(ões) em curso.`}
          action={<LogoutButton all label="Terminar todas" />}
        />
        <ul className="divide-mist/70 divide-y">
          {sessions.slice(0, 12).map((session) => {
            const flags = [
              session.metadata?.new_device && 'novo dispositivo',
              session.metadata?.new_ip && 'novo IP',
              session.metadata?.new_country && 'novo país',
            ].filter(Boolean) as string[];
            return (
              <li key={session.id} className="flex flex-wrap items-center justify-between gap-3 px-5 py-3">
                <div className="flex items-start gap-3">
                  <MonitorSmartphone className="text-navy/40 mt-0.5 size-4.5 shrink-0" aria-hidden />
                  <div>
                    <p className="text-navy text-sm font-medium">{session.device || 'Dispositivo desconhecido'}</p>
                    <p className="text-navy/55 mt-0.5 text-xs">
                      {[
                        session.ip_address,
                        session.country_code || null,
                        `última atividade ${formatDateTime(session.last_activity_at)}`,
                      ]
                        .filter(Boolean)
                        .join(' · ')}
                    </p>
                    {flags.length ? (
                      <span className="mt-1 inline-flex">
                        <Badge tone="warning">{flags.join(' · ')}</Badge>
                      </span>
                    ) : null}
                  </div>
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
            );
          })}
        </ul>
      </Card>

      <Card>
        <CardHeader title="Histórico de acessos" description="Os acessos mais recentes à sua conta." />
        {history.length === 0 ? (
          <EmptyState title="Sem registos" />
        ) : (
          <ul className="divide-mist/70 divide-y">
            {history.map((event) => {
              const flags = [
                event.new_device && 'novo dispositivo',
                event.new_ip && 'novo IP',
                event.new_country && 'novo país',
              ].filter(Boolean) as string[];
              return (
                <li key={event.id} className="flex flex-wrap items-center justify-between gap-3 px-5 py-3">
                  <div>
                    <p className="text-navy text-sm font-medium">{EVENT_LABELS[event.event_type] ?? event.event_type}</p>
                    <p className="text-navy/55 mt-0.5 text-xs">
                      {[event.ip_address, event.country_code || null, event.device]
                        .filter(Boolean)
                        .join(' · ')}
                    </p>
                    {flags.length ? (
                      <span className="mt-1 inline-flex">
                        <Badge tone="warning">{flags.join(' · ')}</Badge>
                      </span>
                    ) : null}
                  </div>
                  <div className="text-right">
                    <Badge tone={STATUS_TONE[event.status as keyof typeof STATUS_TONE] ?? 'neutral'}>
                      {event.status === 'success' ? 'sucesso' : event.status === 'failed' ? 'falhou' : 'bloqueado'}
                    </Badge>
                    <p className="text-navy/40 mt-1 text-xs">{formatDateTime(event.created_at)}</p>
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </Card>
    </>
  );
}
