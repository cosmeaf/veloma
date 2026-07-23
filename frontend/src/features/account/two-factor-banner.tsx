'use client';

import { ShieldAlert, X } from 'lucide-react';
import Link from 'next/link';
import { useState } from 'react';

const DISMISS_KEY = 'veloma:2fa-reminder-dismissed';

/**
 * Proactive reminder shown on the dashboard when the account has no two-factor
 * enabled. Dismissible per browser; the link goes straight to Security.
 */
export function TwoFactorBanner({ enabled, href }: { enabled: boolean; href: string }) {
  const [hidden, setHidden] = useState(false);

  if (enabled || hidden) return null;
  // Respect a previous dismissal without blocking first render.
  if (typeof window !== 'undefined' && window.localStorage.getItem(DISMISS_KEY) === '1') return null;

  return (
    <div className="border-gold-high/60 bg-gold-high/15 flex flex-wrap items-center gap-3 rounded-xl border px-4 py-3">
      <span className="bg-navy inline-flex size-9 shrink-0 items-center justify-center rounded-lg">
        <ShieldAlert className="text-gold size-4.5" aria-hidden />
      </span>
      <div className="min-w-0 flex-1">
        <p className="text-navy text-sm font-medium">Proteja a sua conta com verificação em duas etapas</p>
        <p className="text-navy/70 mt-0.5 text-xs">
          A sua conta ainda não tem 2FA. Ative para receber um código por e-mail em cada início de sessão.
        </p>
      </div>
      <Link
        href={href}
        className="bg-navy text-ivory hover:bg-navy-soft rounded-lg px-3.5 py-2 text-sm font-medium whitespace-nowrap transition-colors"
      >
        Ativar agora
      </Link>
      <button
        type="button"
        aria-label="Dispensar"
        className="text-navy/40 hover:text-navy"
        onClick={() => {
          window.localStorage.setItem(DISMISS_KEY, '1');
          setHidden(true);
        }}
      >
        <X className="size-4" />
      </button>
    </div>
  );
}
