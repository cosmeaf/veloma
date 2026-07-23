import type { Metadata } from 'next';
import { redirect } from 'next/navigation';

import { AuthShell } from '@/components/auth-shell';
import { FirstAccessForm } from '@/features/authentication/first-access-form';
import { getCurrentUser, homePathFor } from '@/lib/auth/session';

export const metadata: Metadata = { title: 'Primeiro acesso' };

export default async function FirstAccessPage() {
  const user = await getCurrentUser();
  if (!user) redirect('/entrar?next=/primeiro-acesso');
  if (!user.must_change_credentials) redirect(homePathFor(user));

  return (
    <AuthShell
      title="Primeiro acesso"
      description="Esta conta foi criada com credenciais temporárias partilhadas. Defina as suas antes de continuar."
      width="md"
    >
      <FirstAccessForm currentEmail={user.email} />
    </AuthShell>
  );
}
