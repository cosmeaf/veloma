'use client';

import { ChevronLeft, Menu, X } from 'lucide-react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useEffect, useState, type ReactNode } from 'react';

import { VelomaMark, VelomaSymbol } from '@/components/brand';
import { HeaderActions } from '@/components/header-actions';
import { LogoutButton } from '@/components/logout-button';
import { cn } from '@/components/ui';
import { site } from '@/content/site';
import { NAVIGATION_BY_AREA, isActive, type Area } from '@/config/navigation';

const COLLAPSE_KEY = 'veloma:sidebar:collapsed';

/**
 * Navy sidebar shell used by both areas.
 *
 * Collapsible on desktop (icons only), a slide-over drawer on mobile. The
 * navigation is data-driven so a new module only adds an entry.
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
  const [collapsed, setCollapsed] = useState(false);
  const sections = NAVIGATION_BY_AREA[area];

  useEffect(() => setOpen(false), [pathname]);
  useEffect(() => {
    setCollapsed(window.localStorage.getItem(COLLAPSE_KEY) === '1');
  }, []);

  function toggleCollapsed() {
    setCollapsed((current) => {
      const next = !current;
      window.localStorage.setItem(COLLAPSE_KEY, next ? '1' : '0');
      return next;
    });
  }

  const nav = (mini: boolean) => (
    <nav className="flex flex-1 flex-col gap-6 overflow-y-auto px-3 py-4">
      {sections.map((section) => (
        <div key={section.title}>
          {!mini ? (
            <p className="text-gold-high/60 px-3 pb-2 text-xs font-semibold tracking-wider uppercase">
              {section.title}
            </p>
          ) : (
            <div className="mx-3 mb-2 h-px bg-white/10" />
          )}
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
                    title={mini ? link.label : undefined}
                    className={cn(
                      'flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                      mini && 'justify-center px-0',
                      active ? 'bg-gold text-navy shadow-sm' : 'text-ivory/75 hover:bg-white/10 hover:text-ivory',
                    )}
                  >
                    <Icon className="size-4 shrink-0" aria-hidden />
                    {!mini ? link.label : null}
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
      {/* Desktop sidebar — collapsible */}
      <aside
        className={cn(
          'bg-navy hidden shrink-0 flex-col border-r border-white/10 transition-[width] duration-200 lg:flex',
          collapsed ? 'w-16' : 'w-64',
        )}
      >
        <div className={cn('flex h-14 items-center border-b border-white/10', collapsed ? 'justify-center px-2' : 'gap-2 px-5')}>
          <Link href="/" aria-label={site.name}>
            {collapsed ? <VelomaSymbol tone="dark" className="h-6" /> : <VelomaMark tone="dark" />}
          </Link>
          {!collapsed ? (
            <span className="bg-white/10 text-gold-high rounded-full px-2 py-0.5 text-xs font-medium">{scope}</span>
          ) : null}
        </div>
        {nav(collapsed)}
        <button
          type="button"
          onClick={toggleCollapsed}
          className="text-ivory/50 hover:bg-white/10 hover:text-ivory flex items-center justify-center gap-2 border-t border-white/10 py-2 text-xs"
          aria-label={collapsed ? 'Expandir menu' : 'Recolher menu'}
        >
          <ChevronLeft className={cn('size-4 transition-transform', collapsed && 'rotate-180')} />
          {!collapsed ? 'Recolher' : null}
        </button>
        <div className={cn('flex items-center gap-2 border-t border-white/10 py-3', collapsed ? 'justify-center px-2' : 'justify-between px-4')}>
          {!collapsed ? <p className="text-ivory/70 min-w-0 flex-1 truncate text-sm">{userName}</p> : null}
          <LogoutButton onNavy iconOnly={collapsed} />
        </div>
      </aside>

      {/* Mobile drawer */}
      {open ? (
        <div className="fixed inset-0 z-40 lg:hidden">
          <button type="button" aria-label="Fechar menu" className="bg-navy/60 absolute inset-0" onClick={() => setOpen(false)} />
          <aside className="bg-navy absolute inset-y-0 left-0 flex w-64 flex-col shadow-xl">
            <div className="flex h-14 items-center justify-between border-b border-white/10 px-5">
              <VelomaMark tone="dark" />
              <button type="button" onClick={() => setOpen(false)} aria-label="Fechar menu">
                <X className="text-ivory/70 size-5" />
              </button>
            </div>
            {nav(false)}
            <div className="flex items-center justify-between gap-2 border-t border-white/10 px-4 py-3">
              <p className="text-ivory/70 min-w-0 flex-1 truncate text-sm">{userName}</p>
              <LogoutButton onNavy />
            </div>
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
          <div className="ml-auto flex items-center gap-2">
            {headerAction}
            <HeaderActions />
          </div>
        </header>
        <main className="w-full flex-1 space-y-6 px-4 py-8 sm:px-6 lg:px-8">{children}</main>
      </div>
    </div>
  );
}
