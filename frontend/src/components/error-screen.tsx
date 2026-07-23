import type { ReactNode } from 'react';

/**
 * Full-screen navy error state, shared by the 404 and error boundaries.
 * Never surfaces a stack trace or framework detail to the visitor.
 */
export function ErrorScreen({
  code,
  heading,
  message,
  action,
}: {
  code: string;
  heading: string;
  message: string;
  action?: ReactNode;
}) {
  return (
    <main className="bg-navy text-ivory flex min-h-screen flex-1 items-center justify-center px-6 py-16 text-center">
      <div>
        <div className="text-gold-high text-sm font-bold tracking-[0.18em] uppercase">Veloma</div>
        <div className="text-gold-high font-display mt-4 text-6xl font-semibold">{code}</div>
        <h1 className="font-display mt-1 text-2xl font-semibold">{heading}</h1>
        <p className="text-ivory/65 mx-auto mt-2 max-w-md text-sm">{message}</p>
        {action ? <div className="mt-6">{action}</div> : null}
      </div>
    </main>
  );
}
