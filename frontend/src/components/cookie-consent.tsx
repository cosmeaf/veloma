'use client';

import { Cookie } from 'lucide-react';
import Link from 'next/link';
import { useEffect, useState } from 'react';

const CONSENT_KEY = 'veloma:cookie-consent';

/**
 * Privacy-first cookie notice. The Platform only uses strictly necessary
 * cookies, so this records acknowledgement rather than offering trackers to
 * opt into. Renders nothing until mounted to avoid hydration mismatch.
 */
export function CookieConsent() {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (window.localStorage.getItem(CONSENT_KEY) !== '1') setVisible(true);
  }, []);

  if (!visible) return null;

  function accept() {
    window.localStorage.setItem(CONSENT_KEY, '1');
    setVisible(false);
  }

  return (
    <div className="fixed inset-x-0 bottom-0 z-50 px-4 pb-4">
      <div className="border-mist mx-auto flex max-w-3xl flex-wrap items-center gap-4 rounded-xl border bg-white px-5 py-4 shadow-lg">
        <span className="bg-navy inline-flex size-9 shrink-0 items-center justify-center rounded-lg">
          <Cookie className="text-gold size-4.5" aria-hidden />
        </span>
        <p className="text-navy/75 min-w-0 flex-1 text-sm leading-relaxed">
          Utilizamos apenas cookies estritamente necessários para o funcionamento seguro da plataforma. Saiba mais na{' '}
          <Link href="/cookies" className="text-navy font-medium underline">
            Política de Cookies
          </Link>
          .
        </p>
        <button
          type="button"
          onClick={accept}
          className="bg-navy text-ivory hover:bg-navy-soft rounded-lg px-4 py-2 text-sm font-medium whitespace-nowrap transition-colors"
        >
          Aceitar
        </button>
      </div>
    </div>
  );
}
