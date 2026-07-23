'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

import { cn } from '@/components/ui';

const TABS = [
  { href: '/staff/clientes', label: 'Empresas' },
  { href: '/staff/clientes/convites', label: 'Convites' },
];

/** In-page tabs so clients and invitations share one place in the sidebar. */
export function ClientTabs() {
  const pathname = usePathname();
  return (
    <div className="border-mist flex gap-1 border-b">
      {TABS.map((tab) => {
        const active = pathname === tab.href;
        return (
          <Link
            key={tab.href}
            href={tab.href}
            className={cn(
              '-mb-px border-b-2 px-4 py-2 text-sm font-medium transition-colors',
              active
                ? 'border-gold text-navy'
                : 'text-navy/55 hover:text-navy border-transparent',
            )}
          >
            {tab.label}
          </Link>
        );
      })}
    </div>
  );
}
