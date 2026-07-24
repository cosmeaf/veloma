'use client';

import { Bell, Volume2, VolumeX } from 'lucide-react';
import Link from 'next/link';
import { useEffect, useRef, useState } from 'react';

import { cn } from '@/components/ui';
import { useTheme } from '@/components/theme-provider';

type Notification = { id: string; title: string; body: string; url: string; created_at: string };

/** Bell (system notifications), sound toggle and theme toggle for the header. */
export function HeaderActions() {
  const { soundEnabled, setSoundEnabled, playSound } = useTheme();
  const [open, setOpen] = useState(false);
  const [items, setItems] = useState<Notification[]>([]);
  const [unread, setUnread] = useState(0);
  const ref = useRef<HTMLDivElement>(null);

  async function load() {
    const response = await fetch('/api/portal/notifications', { cache: 'no-store' }).catch(() => null);
    if (!response?.ok) return;
    const payload = await response.json();
    const previous = unread;
    setItems(payload.data?.notifications ?? []);
    setUnread(payload.data?.unread ?? 0);
    if ((payload.data?.unread ?? 0) > previous && previous >= 0) playSound();
  }

  useEffect(() => {
    void load();
    const timer = setInterval(load, 60_000); // poll once a minute
    return () => clearInterval(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    function onClick(event: MouseEvent) {
      if (ref.current && !ref.current.contains(event.target as Node)) setOpen(false);
    }
    document.addEventListener('mousedown', onClick);
    return () => document.removeEventListener('mousedown', onClick);
  }, []);

  async function openBell() {
    const next = !open;
    setOpen(next);
    if (next && unread > 0) {
      await fetch('/api/portal/notifications', { method: 'POST' });
      setUnread(0);
    }
  }

  async function markAllRead() {
    await fetch('/api/portal/notifications', { method: 'POST' });
    setUnread(0);
  }

  async function clearAll() {
    await fetch('/api/portal/notifications', { method: 'DELETE' });
    setItems([]);
    setUnread(0);
  }

  const iconBtn = 'relative rounded-lg p-2 text-ivory/80 hover:bg-white/10 hover:text-ivory transition-colors';

  return (
    <div className="flex items-center gap-1">
      {/* Bell */}
      <div ref={ref} className="relative">
        <button type="button" className={iconBtn} onClick={openBell} aria-label="Notificações">
          <Bell className="size-5" />
          {unread > 0 ? (
            <span className="bg-gold text-navy absolute -top-0.5 -right-0.5 flex min-w-4 items-center justify-center rounded-full px-1 text-[10px] font-bold">
              {unread > 9 ? '9+' : unread}
            </span>
          ) : null}
        </button>
        {open ? (
          <div className="border-mist absolute right-0 z-50 mt-2 w-80 rounded-xl border bg-white shadow-xl">
            <div className="border-mist border-b px-4 py-2.5">
              <p className="text-navy text-sm font-semibold">Notificações</p>
            </div>
            <ul className="max-h-96 overflow-y-auto">
              {items.length === 0 ? (
                <li className="text-navy/55 px-4 py-8 text-center text-sm">Sem notificações.</li>
              ) : (
                items.map((item) => (
                  <li key={item.id} className="border-mist/60 border-b last:border-0">
                    <Link href={item.url} onClick={() => setOpen(false)} className="hover:bg-mist/30 block px-4 py-3">
                      <p className="text-navy text-sm font-medium">{item.title}</p>
                      <p className="text-navy/55 mt-0.5 truncate text-xs">{item.body}</p>
                    </Link>
                  </li>
                ))
              )}
            </ul>
            {items.length ? (
              <div className="border-mist flex items-center justify-between border-t px-4 py-2">
                <button type="button" onClick={markAllRead} className="text-navy/70 hover:text-navy text-xs font-medium">
                  Marcar como lido
                </button>
                <button type="button" onClick={clearAll} className="text-xs font-medium text-red-600 hover:text-red-700">
                  Apagar tudo
                </button>
              </div>
            ) : null}
          </div>
        ) : null}
      </div>

      {/* Sound */}
      <button
        type="button"
        className={iconBtn}
        onClick={() => setSoundEnabled(!soundEnabled)}
        aria-label={soundEnabled ? 'Desativar som' : 'Ativar som'}
        title={soundEnabled ? 'Som ativo' : 'Som desativado'}
      >
        {soundEnabled ? <Volume2 className="size-5" /> : <VolumeX className="size-5" />}
      </button>

    </div>
  );
}
