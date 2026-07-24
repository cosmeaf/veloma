import Image from 'next/image';

import { cn } from '@/components/ui';

/**
 * Brand assets — the client's own logo signature ("V ELOMA — Contabilidade e
 * Consultoria Fiscal LDA", navy with gold accents).
 *
 * The artwork is dark on a transparent background, so it only reads on light
 * surfaces. On dark surfaces (the navy sidebar, the login panel) it sits on a
 * light chip so it stays legible — `tone="dark"` switches that on.
 */
const LOGO_SRC = '/logo_veloma.png';
const LOGO_ALT = 'Veloma — Contabilidade e Consultoria Fiscal';

/** Compact square emblem — used as the collapsed sidebar icon. */
export function VelomaSymbol({
  className,
  tone = 'light',
  title = LOGO_ALT,
}: {
  className?: string;
  tone?: 'light' | 'dark';
  title?: string;
}) {
  return (
    <span className={cn('inline-flex shrink-0 items-center justify-center', tone === 'dark' && 'rounded-md bg-white p-0.5')}>
      <Image src={LOGO_SRC} alt={title} width={64} height={64} className={cn('h-6 w-auto', className)} />
    </span>
  );
}

/** Full signature — used on the login panel and the landing hero. */
export function VelomaLogomark({
  tone = 'light',
  width = 200,
  className,
  priority = false,
}: {
  tone?: 'light' | 'dark';
  width?: number;
  className?: string;
  priority?: boolean;
}) {
  return (
    <span className={cn('inline-flex', tone === 'dark' && 'rounded-2xl bg-white p-4 shadow-sm', className)}>
      <Image src={LOGO_SRC} alt={LOGO_ALT} width={width} height={width} priority={priority} className="h-auto w-full" />
    </span>
  );
}

/** Compact lockup for headers. */
export function VelomaMark({ tone = 'light', className }: { tone?: 'light' | 'dark'; className?: string }) {
  return (
    <span
      className={cn('inline-flex items-center', tone === 'dark' && 'rounded-lg bg-white px-1.5 py-1', className)}
    >
      <Image src={LOGO_SRC} alt={LOGO_ALT} width={80} height={80} className="h-8 w-auto" priority />
    </span>
  );
}
