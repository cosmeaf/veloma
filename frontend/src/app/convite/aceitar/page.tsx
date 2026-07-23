import type { Metadata } from 'next';
import Link from 'next/link';

import { AuthShell } from '@/components/auth-shell';
import { Alert } from '@/components/ui';
import { AcceptInvitationForm } from '@/features/invitations/accept-form';
import { BackendError, backendFetch } from '@/lib/api/backend';

export const metadata: Metadata = { title: 'Aceitar convite' };

type ValidationResult = {
  valid: boolean;
  email: string;
  role: string;
  client_name: string;
  expires_at: string;
};

export default async function AcceptInvitationPage({
  searchParams,
}: {
  searchParams: Promise<{ token?: string }>;
}) {
  const { token } = await searchParams;

  let invitation: ValidationResult | null = null;
  let error: string | null = null;

  if (!token) {
    error = 'O link do convite está incompleto.';
  } else {
    try {
      const payload = await backendFetch<ValidationResult>('/api/client-portal/invitations/validate/', {
        method: 'POST',
        body: JSON.stringify({ token }),
      });
      invitation = payload.data as ValidationResult;
    } catch (caught) {
      error = caught instanceof BackendError ? caught.message : 'Não foi possível validar o convite.';
    }
  }

  return (
    <AuthShell
      title="Criar a sua conta"
      description="Complete os dados para aceder à área de cliente."
      width="md"
    >
      {invitation && token ? (
        <AcceptInvitationForm token={token} email={invitation.email} clientName={invitation.client_name} />
      ) : (
        <div className="space-y-4">
          <Alert>{error}</Alert>
          <p className="text-navy/60 text-sm">
            Peça um novo convite ao seu contabilista, ou{' '}
            <Link href="/entrar" className="text-navy font-medium hover:underline">
              entre
            </Link>{' '}
            se já tem conta.
          </p>
        </div>
      )}
    </AuthShell>
  );
}
