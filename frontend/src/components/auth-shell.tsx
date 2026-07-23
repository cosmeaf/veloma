import Link from 'next/link';
import type { ReactNode } from 'react';

import { VelomaLogomark } from '@/components/brand';
import { site } from '@/content/site';

/**
 * Navy backdrop for every authentication screen, with a light card at the
 * centre. Keeps the entry flow visually part of the brand.
 */
export function AuthShell({
  title,
  description,
  children,
  footer,
  width = 'sm',
}: {
  title: string;
  description?: string;
  children: ReactNode;
  footer?: ReactNode;
  width?: 'sm' | 'md';
}) {
  return (
    <main className="bg-navy flex flex-1 items-center justify-center px-6 py-16">
      <div className={width === 'md' ? 'w-full max-w-xl' : 'w-full max-w-sm'}>
        <Link href="/" aria-label={site.name} className="mx-auto block w-fit">
          <VelomaLogomark tone="dark" width={150} priority />
        </Link>
        <h1 className="font-display text-ivory mt-6 text-center text-2xl font-semibold tracking-tight">{title}</h1>
        {description ? <p className="text-ivory/60 mt-1 text-center text-sm">{description}</p> : null}

        <div className="border-mist mt-6 rounded-xl border bg-white p-6 shadow-xl">{children}</div>

        {footer ? <div className="text-ivory/70 mt-4 text-center text-sm">{footer}</div> : null}
      </div>
    </main>
  );
}
