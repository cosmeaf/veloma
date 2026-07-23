'use client';

import { LogOut } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useState } from 'react';

import { Button } from '@/components/ui';

export function LogoutButton({ all = false, label = 'Sair' }: { all?: boolean; label?: string }) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);

  async function logout() {
    setBusy(true);
    await fetch('/api/auth/logout', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ all }),
    });
    router.replace('/entrar');
    router.refresh();
  }

  return (
    <Button variant="secondary" size="sm" onClick={logout} disabled={busy}>
      <LogOut className="size-4" aria-hidden />
      {label}
    </Button>
  );
}
