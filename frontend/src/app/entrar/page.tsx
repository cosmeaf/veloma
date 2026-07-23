import type { Metadata } from 'next';
import Link from 'next/link';

import { AuthShell } from '@/components/auth-shell';
import { LoginForm } from '@/features/authentication/login-form';

export const metadata: Metadata = { title: 'Entrar' };

export default async function LoginPage({ searchParams }: { searchParams: Promise<{ next?: string }> }) {
  const { next } = await searchParams;

  return (
    <AuthShell
      title="Entrar"
      description="Área reservada a clientes e equipa Veloma."
      footer={
        <>
          <Link href="/recuperar" className="text-ivory font-medium hover:underline">
            Esqueceu-se da palavra-passe?
          </Link>
          <p className="text-ivory/50 mt-2 text-xs">O acesso é criado por convite do seu contabilista.</p>
        </>
      }
    >
      <LoginForm next={next} />
    </AuthShell>
  );
}
