import type { Metadata } from 'next';
import Link from 'next/link';

import { LoginForm } from '@/features/authentication/login-form';
import { VelomaLogomark } from '@/components/brand';
import { site } from '@/content/site';

export const metadata: Metadata = { title: 'Entrar' };

export default async function LoginPage({ searchParams }: { searchParams: Promise<{ next?: string }> }) {
  const { next } = await searchParams;

  return (
    <main className="flex flex-1 items-center justify-center px-6 py-16">
      <div className="w-full max-w-sm">
        <Link href="/" aria-label={site.name} className="mx-auto block w-fit">
          <VelomaLogomark width={150} priority />
        </Link>
        <h1 className="font-display mt-6 text-center text-2xl font-semibold tracking-tight text-navy">Entrar</h1>
        <p className="text-navy/55 mt-1 text-center text-sm">Área reservada a clientes e equipa Veloma.</p>

        <div className="mt-6 rounded-xl border border-mist bg-white p-6">
          <LoginForm next={next} />
        </div>

        <p className="mt-4 text-center text-sm text-navy/55">
          <Link href="/recuperar" className="font-medium text-navy hover:underline">
            Esqueceu-se da palavra-passe?
          </Link>
        </p>
        <p className="mt-2 text-center text-xs text-navy/55">
          O acesso é criado por convite do seu contabilista.
        </p>
      </div>
    </main>
  );
}
