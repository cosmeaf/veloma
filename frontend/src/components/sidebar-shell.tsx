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
 * Sidebar shell used by both areas.
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

  // Any navigation closes the mobile drawer.
  useEffect(() => setOpen(false), [pathname]);

  const nav = (
    <nav className="flex flex-1 flex-col gap-6 overflow-y-auto px-3 py-4">
      {sections.map((section) => (
        <div key={section.title}>
          <p className="text-navy/40 px-3 pb-2 text-xs font-semibold tracking-wider uppercase">{section.title}</p>
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
                      active ? 'bg-navy text-ivory' : 'text-navy/70 hover:bg-mist/50 hover:text-navy',
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
      <aside className="border-mist hidden w-64 shrink-0 flex-col border-r bg-white lg:flex">
        <div className="border-mist flex h-14 items-center gap-2 border-b px-5">
          <Link href="/" aria-label={site.name}>
            <VelomaMark />
          </Link>
          <span className="bg-mist/60 text-navy/70 rounded-full px-2 py-0.5 text-xs font-medium">{scope}</span>
        </div>
        {nav}
        <div className="border-mist border-t px-5 py-3">
          <p className="text-navy/70 truncate text-sm">{userName}</p>
        </div>
      </aside>

      {open ? (
        <div className="fixed inset-0 z-40 lg:hidden">
          <button
            type="button"
            aria-label="Fechar menu"
            className="bg-navy/40 absolute inset-0"
            onClick={() => setOpen(false)}
          />
          <aside className="absolute inset-y-0 left-0 flex w-64 flex-col bg-white shadow-xl">
            <div className="border-mist flex h-14 items-center justify-between border-b px-5">
              <VelomaMark />
              <button type="button" onClick={() => setOpen(false)} aria-label="Fechar menu">
                <X className="text-navy/55 size-5" />
              </button>
            </div>
            {nav}
          </aside>
        </div>
      ) : null}

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="border-mist flex h-14 items-center justify-between gap-3 border-b bg-white px-4 sm:px-6">
          <button
            type="button"
            className="text-navy/70 hover:bg-mist/50 rounded-lg p-2 lg:hidden"
            onClick={() => setOpen(true)}
            aria-label="Abrir menu"
          >
            <Menu className="size-5" />
          </button>
          <span className="text-navy/55 text-sm lg:hidden">{scope}</span>
          <div className="ml-auto flex items-center gap-3">
            {headerAction}
            <span className="text-navy/70 hidden text-sm sm:inline">{userName}</span>
            <LogoutButton />
          </div>
        </header>
        {/* Full width: dense tables and the folder explorer need the room. */}
        <main className="w-full flex-1 space-y-6 px-4 py-8 sm:px-6 lg:px-8">{children}</main>
      </div>
    </div>
  );
}
