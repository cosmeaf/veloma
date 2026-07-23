'use client';

import { Menu, X } from 'lucide-react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useEffect, useState, type ReactNode } from 'react';

import { VelomaMark } from '@/components/brand';
import { LogoutButton } from '@/components/logout-button';
import { cn } from '@/components/ui';
import { site } from '@/content/site';
import { NAVIGATION_BY_AREA, isActive, type Area } from '@/config/navigation';

/**
 * Navy sidebar shell used by both areas.
 *
 * The navigation lives here rather than in the layout because entries carry
 * icon components, and functions cannot cross the server/client boundary. A new
 * module only adds an entry in `config/navigation.ts`.
 */
export function SidebarShell({
  area,
  userName,
  scope,
  headerAction,
  children,
}: {
  area: Area;
  userName: string;
  scope: string;
  headerAction?: ReactNode;
  children: ReactNode;
}) {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const sections = NAVIGATION_BY_AREA[area];

  useEffect(() => setOpen(false), [pathname]);

  const nav = (
    <nav className="flex flex-1 flex-col gap-6 overflow-y-auto px-3 py-4">
      {sections.map((section) => (
        <div key={section.title}>
          <p className="text-gold-high/60 px-3 pb-2 text-xs font-semibold tracking-wider uppercase">{section.title}</p>
          <ul className="space-y-0.5">
            {section.links.map((link) => {
              const active = isActive(pathname, link);
              const Icon = link.icon;
              return (
                <li key={link.href}>
                  <Link
                    href={link.href}
                    data-tour={link.tour}
                    aria-current={active ? 'page' : undefined}
                    className={cn(
                      'flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                      active
                        ? 'bg-gold text-navy shadow-sm'
                        : 'text-ivory/75 hover:bg-white/10 hover:text-ivory',
                    )}
                  >
                    <Icon className="size-4 shrink-0" aria-hidden />
                    {link.label}
                  </Link>
                </li>
              );
            })}
          </ul>
        </div>
      ))}
    </nav>
  );

  return (
    <div className="flex min-h-full flex-1">
      {/* Desktop sidebar — navy with a gold hairline */}
      <aside className="bg-navy hidden w-64 shrink-0 flex-col border-r border-white/10 lg:flex">
        <div className="flex h-14 items-center gap-2 border-b border-white/10 px-5">
          <Link href="/" aria-label={site.name}>
            <VelomaMark tone="dark" />
          </Link>
          <span className="bg-white/10 text-gold-high rounded-full px-2 py-0.5 text-xs font-medium">{scope}</span>
        </div>
        {nav}
        <div className="border-t border-white/10 px-5 py-3">
          <p className="text-ivory/70 truncate text-sm">{userName}</p>
        </div>
      </aside>

      {/* Mobile drawer */}
      {open ? (
        <div className="fixed inset-0 z-40 lg:hidden">
          <button
            type="button"
            aria-label="Fechar menu"
            className="bg-navy/60 absolute inset-0"
            onClick={() => setOpen(false)}
          />
          <aside className="bg-navy absolute inset-y-0 left-0 flex w-64 flex-col shadow-xl">
            <div className="flex h-14 items-center justify-between border-b border-white/10 px-5">
              <VelomaMark tone="dark" />
              <button type="button" onClick={() => setOpen(false)} aria-label="Fechar menu">
                <X className="text-ivory/70 size-5" />
              </button>
            </div>
            {nav}
          </aside>
        </div>
      ) : null}

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="bg-navy flex h-14 items-center justify-between gap-3 px-4 sm:px-6">
          <button
            type="button"
            className="text-ivory/80 rounded-lg p-2 hover:bg-white/10 lg:hidden"
            onClick={() => setOpen(true)}
            aria-label="Abrir menu"
          >
            <Menu className="size-5" />
          </button>
          <span className="text-ivory/70 text-sm lg:hidden">{scope}</span>
          <div className="ml-auto flex items-center gap-3">
            {headerAction}
            <span className="text-ivory/80 hidden text-sm sm:inline">{userName}</span>
            <LogoutButton onNavy />
          </div>
        </header>
        {/* Full width: dense tables and the folder explorer need the room. */}
        <main className="w-full flex-1 space-y-6 px-4 py-8 sm:px-6 lg:px-8">{children}</main>
      </div>
    </div>
  );
}
