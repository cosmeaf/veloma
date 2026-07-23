import type { Metadata } from 'next';
import Link from 'next/link';

import { AuthShell } from '@/components/auth-shell';
import { RecoveryForm } from '@/features/authentication/recovery-form';

export const metadata: Metadata = { title: 'Recuperar acesso' };

export default function RecoveryPage() {
  return (
    <AuthShell
      title="Recuperar acesso"
      description="Enviamos um código para o e-mail da conta."
      footer={
        <Link href="/entrar" className="text-ivory font-medium hover:underline">
          Voltar a entrar
        </Link>
      }
    >
      <RecoveryForm />
    </AuthShell>
  );
}
