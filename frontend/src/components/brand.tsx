import Image from 'next/image';

import { cn } from '@/components/ui';

/**
 * Brand assets.
 *
 * The manual forbids recomposing the logomark with live text, so the full
 * signature is always the vector file. The symbol below is the same vector
 * geometry, rendered flat: the metallic version may not be used under 48 px,
 * and at small sizes the gold reads as "ouro sol" (#B87F07) on light
 * backgrounds and "ouro alto" (#F3D994) on dark ones.
 */
const SYMBOL_PATHS = [
  'M 7.52 22.00 L 28.48 22.00 L 59.55 88.81 L 56.45 127.19 Z',
  'M 56.45 127.19 L 59.55 88.81 L 90.77 11.50 L 109.23 -3.50 Z',
];

export function VelomaSymbol({
  className,
  tone = 'light',
  title = 'Veloma',
}: {
  className?: string;
  tone?: 'light' | 'dark';
  title?: string;
}) {
  return (
    <svg
      viewBox="0 -6 117 136"
      role="img"
      aria-label={title}
      className={cn('h-6 w-auto shrink-0', className)}
      fill={tone === 'dark' ? '#F3D994' : '#B87F07'}
    >
      {SYMBOL_PATHS.map((d) => (
        <path key={d} d={d} />
      ))}
    </svg>
  );
}

/** Full vertical signature. Never below 140 px wide, per the manual. */
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
    <Image
      src={tone === 'dark' ? '/veloma-logomarca-negativo.svg' : '/veloma-logomarca.svg'}
      alt="Veloma — Contabilidade e Consultoria Fiscal"
      width={width}
      height={Math.round((width * 518) / 776)}
      className={className}
      priority={priority}
      // The optimizer refuses SVG unless `dangerouslyAllowSVG` is on; the
      // logomark is a trusted local asset and is served as-is.
      unoptimized
    />
  );
}

/** Compact lockup for headers: flat symbol plus the wordmark set in Cinzel. */
export function VelomaMark({ tone = 'light', className }: { tone?: 'light' | 'dark'; className?: string }) {
  return (
    <span className={cn('flex items-center gap-2', className)}>
      <VelomaSymbol tone={tone} className="h-5" />
      <span
        className={cn(
          'font-display text-sm font-semibold tracking-[0.16em] uppercase',
          tone === 'dark' ? 'text-ivory' : 'text-navy',
        )}
      >
        Veloma
      </span>
    </span>
  );
}
