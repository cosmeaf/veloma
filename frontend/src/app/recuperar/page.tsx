import type { Metadata } from 'next';
import Link from 'next/link';

import { RecoveryForm } from '@/features/authentication/recovery-form';
import { VelomaLogomark } from '@/components/brand';
import { site } from '@/content/site';

export const metadata: Metadata = { title: 'Recuperar acesso' };

export default function RecoveryPage() {
  return (
    <main className="flex flex-1 items-center justify-center px-6 py-16">
      <div className="w-full max-w-sm">
        <Link href="/" aria-label={site.name} className="mx-auto block w-fit">
          <VelomaLogomark width={150} priority />
        </Link>
        <h1 className="font-display mt-6 text-center text-2xl font-semibold tracking-tight text-navy">Recuperar acesso</h1>
        <p className="text-navy/55 mt-1 text-center text-sm">Enviamos um código para o e-mail da conta.</p>

        <div className="mt-6 rounded-xl border border-mist bg-white p-6">
          <RecoveryForm />
        </div>

        <p className="mt-4 text-center text-sm text-navy/55">
          <Link href="/entrar" className="font-medium text-navy hover:underline">
            Voltar a entrar
          </Link>
        </p>
      </div>
    </main>
  );
}
