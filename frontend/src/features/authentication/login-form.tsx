'use client';

import { zodResolver } from '@hookform/resolvers/zod';
import { Loader2 } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useState } from 'react';
import { useForm } from 'react-hook-form';

import { Alert, Button, Field, Input } from '@/components/ui';
import { loginSchema, otpSchema, type LoginInput, type OtpInput } from '@/lib/validation/schemas';

type Stage = { step: 'credentials' } | { step: 'otp'; challengeId: string };

export function LoginForm({ next }: { next?: string }) {
  const router = useRouter();
  const [stage, setStage] = useState<Stage>({ step: 'credentials' });
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const credentials = useForm<LoginInput>({ resolver: zodResolver(loginSchema) });
  const otp = useForm<OtpInput>({ resolver: zodResolver(otpSchema) });

  async function submitCredentials(values: LoginInput) {
    setError(null);
    const response = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(values),
    });
    const payload = await response.json();
    if (!response.ok || !payload.success) {
      setError(payload.message ?? 'Não foi possível autenticar.');
      return;
    }
    if (payload.requires_otp) {
      setStage({ step: 'otp', challengeId: payload.challenge_id });
      setNotice('Enviámos um código de confirmação para o seu e-mail.');
      return;
    }
    router.replace(next ?? (payload.user?.roles?.includes('STAFF') || payload.user?.roles?.includes('STAFF_MANAGER') ? '/staff' : '/dashboard'));
    router.refresh();
  }

  async function submitOtp(values: OtpInput) {
    if (stage.step !== 'otp') return;
    setError(null);
    const response = await fetch('/api/auth/otp', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ challenge_id: stage.challengeId, code: values.code }),
    });
    const payload = await response.json();
    if (!response.ok || !payload.success) {
      setError(payload.message ?? 'Código inválido.');
      return;
    }
    router.replace(next ?? '/dashboard');
    router.refresh();
  }

  async function resendOtp() {
    if (stage.step !== 'otp') return;
    setError(null);
    const response = await fetch('/api/auth/otp', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'resend', challenge_id: stage.challengeId }),
    });
    const payload = await response.json();
    if (!response.ok || !payload.success) {
      setError(payload.message ?? 'Não foi possível reenviar o código.');
      return;
    }
    setStage({ step: 'otp', challengeId: payload.challenge_id });
    setNotice('Enviámos um novo código.');
  }

  if (stage.step === 'otp') {
    return (
      <form onSubmit={otp.handleSubmit(submitOtp)} className="space-y-4">
        {notice ? <Alert tone="info">{notice}</Alert> : null}
        {error ? <Alert>{error}</Alert> : null}
        <Field label="Código de confirmação" error={otp.formState.errors.code?.message}>
          <Input
            {...otp.register('code')}
            inputMode="numeric"
            autoComplete="one-time-code"
            placeholder="000000"
            autoFocus
          />
        </Field>
        <Button type="submit" className="w-full" disabled={otp.formState.isSubmitting}>
          {otp.formState.isSubmitting ? <Loader2 className="size-4 animate-spin" /> : null}
          Confirmar
        </Button>
        <Button type="button" variant="ghost" className="w-full" onClick={resendOtp}>
          Reenviar código
        </Button>
      </form>
    );
  }

  return (
    <form onSubmit={credentials.handleSubmit(submitCredentials)} className="space-y-4">
      {error ? <Alert>{error}</Alert> : null}
      <Field label="E-mail" error={credentials.formState.errors.email?.message}>
        <Input {...credentials.register('email')} type="email" autoComplete="email" placeholder="nome@empresa.pt" autoFocus />
      </Field>
      <Field label="Palavra-passe" error={credentials.formState.errors.password?.message}>
        <Input {...credentials.register('password')} type="password" autoComplete="current-password" />
      </Field>
      <Button type="submit" className="w-full" disabled={credentials.formState.isSubmitting}>
        {credentials.formState.isSubmitting ? <Loader2 className="size-4 animate-spin" /> : null}
        Entrar
      </Button>
    </form>
  );
}
