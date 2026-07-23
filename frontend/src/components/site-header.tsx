import { ArrowRight } from 'lucide-react';
import Link from 'next/link';

import { VelomaMark } from '@/components/brand';

/** Public header used on institutional and legal pages (not the app shell). */
export function SiteHeader() {
  return (
    <header className="bg-navy text-ivory border-b border-white/10">
      <nav className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        <Link href="/" aria-label="Início">
          <VelomaMark tone="dark" />
        </Link>
        <Link
          href="/entrar"
          className="bg-gold text-navy hover:bg-gold-high inline-flex items-center gap-1.5 rounded-lg px-4 py-2 text-sm font-medium transition-colors"
        >
          Área de cliente
          <ArrowRight className="size-4" />
        </Link>
      </nav>
    </header>
  );
}
