'use client';

import { zodResolver } from '@hookform/resolvers/zod';
import { Loader2 } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';

import { Alert, Button, Field, Input } from '@/components/ui';
import {
  otpSchema,
  recoverySchema,
  resetSchema,
  type OtpInput,
  type RecoveryInput,
  type ResetInput,
} from '@/lib/validation/schemas';

type Grant = { uid: string; reset_token: string };
type Stage =
  | { step: 'email' }
  | { step: 'otp'; challengeId: string }
  | { step: 'reset'; grant: Grant }
  | { step: 'done' };

/**
 * Three-step recovery: e-mail → OTP → new password.
 *
 * The uid and the opaque reset token live in component state for the duration
 * of the flow only, exactly as the backend contract describes.
 */
/** Seconds to wait before the code can be resent (matches the backend default). */
const RESEND_COOLDOWN = 60;

export function RecoveryForm() {
  const router = useRouter();
  const [stage, setStage] = useState<Stage>({ step: 'email' });
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [cooldown, setCooldown] = useState(0);
  const [resending, setResending] = useState(false);

  const emailForm = useForm<RecoveryInput>({ resolver: zodResolver(recoverySchema) });
  const otpForm = useForm<OtpInput>({ resolver: zodResolver(otpSchema) });
  const resetForm = useForm<ResetInput>({ resolver: zodResolver(resetSchema) });

  // Tick the resend countdown down to zero.
  useEffect(() => {
    if (cooldown <= 0) return;
    const timer = setTimeout(() => setCooldown((value) => value - 1), 1000);
    return () => clearTimeout(timer);
  }, [cooldown]);

  async function post(body: Record<string, unknown>, endpoint: string) {
    const response = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    return { ok: response.ok, payload: await response.json() };
  }

  async function submitEmail(values: RecoveryInput) {
    setError(null);
    const { ok, payload } = await post({ action: 'recovery', email: values.email }, '/api/auth/password');
    if (!ok || !payload.success) {
      setError(payload.message ?? 'Não foi possível iniciar a recuperação.');
      return;
    }
    setStage({ step: 'otp', challengeId: payload.challenge_id });
    setCooldown(RESEND_COOLDOWN);
  }

  async function resendCode() {
    if (stage.step !== 'otp' || cooldown > 0 || resending) return;
    setError(null);
    setNotice(null);
    setResending(true);
    const { ok, payload } = await post({ action: 'resend', challenge_id: stage.challengeId }, '/api/auth/otp');
    setResending(false);
    if (!ok || !payload.success) {
      setError(payload.message ?? 'Não foi possível reenviar o código.');
      return;
    }
    setStage({ step: 'otp', challengeId: payload.challenge_id ?? stage.challengeId });
    setNotice('Enviámos um novo código para o seu e-mail.');
    setCooldown(RESEND_COOLDOWN);
  }

  async function submitOtp(values: OtpInput) {
    if (stage.step !== 'otp') return;
    setError(null);
    const { ok, payload } = await post({ challenge_id: stage.challengeId, code: values.code }, '/api/auth/otp');
    if (!ok || !payload.success) {
      setError(payload.message ?? 'Código inválido.');
      return;
    }
    setStage({ step: 'reset', grant: { uid: payload.uid, reset_token: payload.reset_token } });
  }

  async function submitReset(values: ResetInput) {
    if (stage.step !== 'reset') return;
    setError(null);
    const { ok, payload } = await post(
      { action: 'reset', ...stage.grant, password: values.password, password2: values.password2 },
      '/api/auth/password',
    );
    if (!ok || !payload.success) {
      setError(payload.message ?? 'Não foi possível definir a nova palavra-passe.');
      return;
    }
    setStage({ step: 'done' });
    setTimeout(() => router.replace('/entrar'), 2500);
  }

  if (stage.step === 'done') {
    return (
      <div className="space-y-4">
        <Alert tone="success">Palavra-passe alterada. Vai ser encaminhado para a página de entrada.</Alert>
      </div>
    );
  }

  if (stage.step === 'reset') {
    return (
      <form onSubmit={resetForm.handleSubmit(submitReset)} className="space-y-4">
        {error ? <Alert>{error}</Alert> : null}
        <Field label="Nova palavra-passe" error={resetForm.formState.errors.password?.message}>
          <Input {...resetForm.register('password')} type="password" autoComplete="new-password" autoFocus />
        </Field>
        <Field label="Repetir palavra-passe" error={resetForm.formState.errors.password2?.message}>
          <Input {...resetForm.register('password2')} type="password" autoComplete="new-password" />
        </Field>
        <Button type="submit" className="w-full" disabled={resetForm.formState.isSubmitting}>
          {resetForm.formState.isSubmitting ? <Loader2 className="size-4 animate-spin" /> : null}
          Definir palavra-passe
        </Button>
      </form>
    );
  }

  if (stage.step === 'otp') {
    return (
      <form onSubmit={otpForm.handleSubmit(submitOtp)} className="space-y-4">
        <Alert tone="info">Se a conta existir, enviámos um código para o e-mail indicado.</Alert>
        {notice ? <Alert tone="success">{notice}</Alert> : null}
        {error ? <Alert>{error}</Alert> : null}
        <Field label="Código de confirmação" error={otpForm.formState.errors.code?.message}>
          <Input
            {...otpForm.register('code')}
            inputMode="numeric"
            autoComplete="one-time-code"
            maxLength={6}
            placeholder="000000"
            autoFocus
            className="text-center font-mono text-2xl tracking-[0.6em]"
          />
        </Field>
        <Button type="submit" className="w-full" disabled={otpForm.formState.isSubmitting}>
          {otpForm.formState.isSubmitting ? <Loader2 className="size-4 animate-spin" /> : null}
          Confirmar código
        </Button>
        <div className="text-center text-sm">
          {cooldown > 0 ? (
            <span className="text-navy/55">Reenviar código em {cooldown}s</span>
          ) : (
            <button
              type="button"
              onClick={resendCode}
              disabled={resending}
              className="text-navy font-medium hover:underline disabled:opacity-60"
            >
              {resending ? 'A reenviar…' : 'Reenviar código'}
            </button>
          )}
        </div>
      </form>
    );
  }

  return (
    <form onSubmit={emailForm.handleSubmit(submitEmail)} className="space-y-4">
      {error ? <Alert>{error}</Alert> : null}
      <Field label="E-mail da conta" error={emailForm.formState.errors.email?.message}>
        <Input {...emailForm.register('email')} type="email" autoComplete="email" autoFocus />
      </Field>
      <Button type="submit" className="w-full" disabled={emailForm.formState.isSubmitting}>
        {emailForm.formState.isSubmitting ? <Loader2 className="size-4 animate-spin" /> : null}
        Recuperar acesso
      </Button>
    </form>
  );
}
