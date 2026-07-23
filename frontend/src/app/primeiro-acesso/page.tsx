import type { Metadata } from 'next';
import Link from 'next/link';
import { redirect } from 'next/navigation';

import { VelomaLogomark } from '@/components/brand';
import { site } from '@/content/site';
import { FirstAccessForm } from '@/features/authentication/first-access-form';
import { getCurrentUser, homePathFor } from '@/lib/auth/session';

export const metadata: Metadata = { title: 'Primeiro acesso' };

export default async function FirstAccessPage() {
  const user = await getCurrentUser();
  if (!user) redirect('/entrar?next=/primeiro-acesso');
  // Nothing to do here once the credentials are the holder's own.
  if (!user.must_change_credentials) redirect(homePathFor(user));

  return (
    <main className="flex flex-1 items-center justify-center px-6 py-16">
      <div className="w-full max-w-md">
        <Link href="/" aria-label={site.name} className="mx-auto block w-fit">
          <VelomaLogomark width={150} priority />
        </Link>
        <h1 className="font-display text-navy mt-6 text-center text-2xl font-semibold tracking-tight">
          Primeiro acesso
        </h1>
        <p className="text-navy/55 mt-1 text-center text-sm">
          Esta conta foi criada com credenciais temporárias partilhadas. Defina as suas antes de continuar.
        </p>

        <div className="border-mist mt-6 rounded-xl border bg-white p-6">
          <FirstAccessForm currentEmail={user.email} />
        </div>
      </div>
    </main>
  );
}
