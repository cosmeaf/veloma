import type { Metadata } from 'next';
import Link from 'next/link';

import { Alert } from '@/components/ui';
import { VelomaLogomark } from '@/components/brand';
import { site } from '@/content/site';
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
    <main className="flex flex-1 items-center justify-center px-6 py-16">
      <div className="w-full max-w-xl">
        <Link href="/" aria-label={site.name} className="mx-auto block w-fit">
          <VelomaLogomark width={150} priority />
        </Link>
        <h1 className="font-display mt-6 text-center text-2xl font-semibold tracking-tight text-navy">Criar a sua conta</h1>
        <p className="text-navy/55 mt-1 text-center text-sm">Complete os dados para aceder à área de cliente.</p>

        <div className="mt-6 rounded-xl border border-mist bg-white p-6">
          {invitation && token ? (
            <AcceptInvitationForm token={token} email={invitation.email} clientName={invitation.client_name} />
          ) : (
            <div className="space-y-4">
              <Alert>{error}</Alert>
              <p className="text-sm text-navy/55">
                Peça um novo convite ao seu contabilista, ou{' '}
                <Link href="/entrar" className="font-medium text-navy hover:underline">
                  entre
                </Link>{' '}
                se já tem conta.
              </p>
            </div>
          )}
        </div>
      </div>
    </main>
  );
}
