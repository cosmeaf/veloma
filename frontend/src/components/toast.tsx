'use client';

import { Check, Info, TriangleAlert, X } from 'lucide-react';
import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from 'react';

import { cn } from '@/components/ui';

type ToastTone = 'success' | 'error' | 'info';
type Toast = { id: number; tone: ToastTone; message: string };

type ToastApi = {
  success: (message: string) => void;
  error: (message: string) => void;
  info: (message: string) => void;
};

const ToastContext = createContext<ToastApi | null>(null);

/** Lightweight, dependency-free toasts for action feedback. */
export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const remove = useCallback((id: number) => setToasts((current) => current.filter((t) => t.id !== id)), []);

  const push = useCallback((tone: ToastTone, message: string) => {
    // Date.now is fine on the client for a transient key.
    const id = Date.now() + Math.random();
    setToasts((current) => [...current, { id, tone, message }]);
  }, []);

  const api: ToastApi = {
    success: (m) => push('success', m),
    error: (m) => push('error', m),
    info: (m) => push('info', m),
  };

  return (
    <ToastContext.Provider value={api}>
      {children}
      <div className="pointer-events-none fixed inset-x-0 bottom-4 z-[60] flex flex-col items-center gap-2 px-4">
        {toasts.map((toast) => (
          <ToastItem key={toast.id} toast={toast} onDone={() => remove(toast.id)} />
        ))}
      </div>
    </ToastContext.Provider>
  );
}

const TONE_STYLES: Record<ToastTone, string> = {
  success: 'border-emerald-200 bg-white text-emerald-800',
  error: 'border-red-200 bg-white text-red-800',
  info: 'border-mist bg-white text-navy',
};

const TONE_ICON = { success: Check, error: TriangleAlert, info: Info };

function ToastItem({ toast, onDone }: { toast: Toast; onDone: () => void }) {
  useEffect(() => {
    const timer = setTimeout(onDone, 4000);
    return () => clearTimeout(timer);
  }, [onDone]);

  const Icon = TONE_ICON[toast.tone];
  return (
    <div
      role="status"
      className={cn(
        'pointer-events-auto flex w-full max-w-sm items-start gap-2.5 rounded-lg border px-3.5 py-2.5 text-sm shadow-lg',
        TONE_STYLES[toast.tone],
      )}
    >
      <Icon className="mt-0.5 size-4 shrink-0" aria-hidden />
      <span className="flex-1">{toast.message}</span>
      <button type="button" onClick={onDone} aria-label="Fechar" className="text-navy/30 hover:text-navy">
        <X className="size-4" />
      </button>
    </div>
  );
}

export function useToast(): ToastApi {
  const context = useContext(ToastContext);
  if (!context) {
    // No provider (e.g. public pages): fail quietly instead of crashing.
    return { success: () => {}, error: () => {}, info: () => {} };
  }
  return context;
}
