import Link from 'next/link';
import type { ButtonHTMLAttributes, InputHTMLAttributes, ReactNode, SelectHTMLAttributes, TextareaHTMLAttributes } from 'react';

export function cn(...values: Array<string | false | null | undefined>): string {
  return values.filter(Boolean).join(' ');
}

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger';
  size?: 'sm' | 'md';
};

const BUTTON_VARIANTS: Record<string, string> = {
  primary: 'bg-navy text-ivory hover:bg-navy-soft disabled:bg-lilac',
  secondary: 'border border-mist bg-white text-navy hover:bg-mist/40 disabled:text-lilac',
  ghost: 'text-navy/70 hover:bg-mist/50 hover:text-navy',
  danger: 'border border-red-200 bg-white text-red-700 hover:bg-red-50',
};

export function Button({ variant = 'primary', size = 'md', className, ...props }: ButtonProps) {
  return (
    <button
      {...props}
      className={cn(
        'inline-flex items-center justify-center gap-2 rounded-lg font-medium transition-colors',
        'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gold-sun',
        'disabled:cursor-not-allowed',
        size === 'sm' ? 'px-3 py-1.5 text-sm' : 'px-4 py-2.5 text-sm',
        BUTTON_VARIANTS[variant],
        className,
      )}
    />
  );
}

export function Field({
  label,
  error,
  hint,
  children,
}: {
  label: string;
  error?: string;
  hint?: string;
  children: ReactNode;
}) {
  return (
    <label className="block space-y-1.5">
      <span className="block text-sm font-medium text-navy/80">{label}</span>
      {children}
      {hint && !error ? <span className="block text-xs text-navy/55">{hint}</span> : null}
      {error ? (
        <span role="alert" className="block text-xs font-medium text-red-600">
          {error}
        </span>
      ) : null}
    </label>
  );
}

const CONTROL =
  'w-full rounded-lg border border-mist bg-white px-3 py-2 text-sm text-navy placeholder:text-navy/40 focus:border-gold-sun focus:outline-none disabled:bg-mist/40';

export function Input({ className, ...props }: InputHTMLAttributes<HTMLInputElement>) {
  return <input {...props} className={cn(CONTROL, className)} />;
}

export function Textarea({ className, ...props }: TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return <textarea {...props} className={cn(CONTROL, 'min-h-24 resize-y', className)} />;
}

export function Select({ className, ...props }: SelectHTMLAttributes<HTMLSelectElement>) {
  return <select {...props} className={cn(CONTROL, className)} />;
}

export function Card({ children, className }: { children: ReactNode; className?: string }) {
  return <div className={cn('rounded-xl border border-mist bg-white', className)}>{children}</div>;
}

export function CardHeader({ title, description, action }: { title: string; description?: string; action?: ReactNode }) {
  return (
    <div className="flex items-start justify-between gap-4 border-b border-mist px-5 py-4">
      <div>
        <h2 className="text-sm font-semibold text-navy">{title}</h2>
        {description ? <p className="mt-0.5 text-sm text-navy/55">{description}</p> : null}
      </div>
      {action}
    </div>
  );
}

const TONES: Record<string, string> = {
  neutral: 'bg-mist/60 text-navy',
  info: 'bg-mist text-navy-soft',
  success: 'bg-emerald-50 text-emerald-700',
  warning: 'bg-gold-high/40 text-gold-deep',
  danger: 'bg-red-50 text-red-700',
};

export type Tone = keyof typeof TONES;

export function Badge({ children, tone = 'neutral' }: { children: ReactNode; tone?: Tone }) {
  return (
    <span className={cn('inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium', TONES[tone])}>
      {children}
    </span>
  );
}

export function Alert({ children, tone = 'danger' }: { children: ReactNode; tone?: Tone }) {
  return (
    <div role="alert" className={cn('rounded-lg px-3 py-2 text-sm', TONES[tone])}>
      {children}
    </div>
  );
}

export function EmptyState({ title, description }: { title: string; description?: string }) {
  return (
    <div className="px-5 py-10 text-center">
      <p className="text-sm font-medium text-navy">{title}</p>
      {description ? <p className="mt-1 text-sm text-navy/55">{description}</p> : null}
    </div>
  );
}

export function StatTile({
  label,
  value,
  tone = 'neutral',
  href,
}: {
  label: string;
  value: number | string;
  tone?: Tone;
  /** When set, the whole tile is a link with hover feedback. */
  href?: string;
}) {
  const inner = (
    <>
      <p className="text-navy/55 text-xs font-medium tracking-wide uppercase">{label}</p>
      <p className={cn('mt-2 text-2xl font-semibold', tone === 'danger' ? 'text-red-600' : 'text-navy')}>{value}</p>
    </>
  );
  const base = 'rounded-xl border border-mist bg-white p-4 block';
  if (href) {
    return (
      <Link
        href={href}
        className={cn(base, 'hover:border-gold-sun/50 hover:shadow-sm transition-all')}
      >
        {inner}
      </Link>
    );
  }
  return <div className={base}>{inner}</div>;
}

export function PageHeader({ title, description, action }: { title: string; description?: string; action?: ReactNode }) {
  return (
    <div className="flex flex-wrap items-end justify-between gap-4">
      <div>
        <h1 className="font-display text-2xl font-semibold tracking-tight text-navy">{title}</h1>
        {description ? <p className="mt-1 text-sm text-navy/55">{description}</p> : null}
      </div>
      {action}
    </div>
  );
}
