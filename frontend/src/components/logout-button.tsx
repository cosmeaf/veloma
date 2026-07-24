'use client';

import { LogOut } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useState } from 'react';

import { Button, cn } from '@/components/ui';

export function LogoutButton({
  all = false,
  label = 'Sair',
  onNavy = false,
  iconOnly = false,
}: {
  all?: boolean;
  label?: string;
  onNavy?: boolean;
  iconOnly?: boolean;
}) {
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
    <Button
      variant="secondary"
      size="sm"
      onClick={logout}
      disabled={busy}
      className={cn(
        // Light pill on the navy sidebar: clearly visible, dark text on light bg.
        onNavy && '!border-transparent !bg-ivory !text-navy hover:!bg-white',
        iconOnly && 'px-2',
      )}
      title={iconOnly ? label : undefined}
      aria-label={label}
    >
      <LogOut className="size-4" aria-hidden />
      {!iconOnly ? label : null}
    </Button>
  );
}
