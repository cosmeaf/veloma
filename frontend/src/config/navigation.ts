import {
  Building2,
  FileStack,
  FolderTree,
  LayoutDashboard,
  ShieldCheck,
  Sparkles,
  Users,
  type LucideIcon,
} from 'lucide-react';

export type NavLink = {
  href: string;
  label: string;
  icon: LucideIcon;
  /** Matches nested routes. Set to false for index links like `/staff`. */
  nested?: boolean;
  /** Anchor used by the guided tour to highlight this entry. */
  tour?: string;
};

export type NavSection = {
  title: string;
  links: NavLink[];
};

/**
 * Staff navigation.
 *
 * A new module is a single entry here — or a new section when it brings its own
 * group of screens. Nothing else in the shell needs to change.
 */
export const STAFF_NAVIGATION: NavSection[] = [
  {
    title: 'Operação',
    links: [
      { href: '/staff', label: 'Resumo', icon: LayoutDashboard, nested: false },
      { href: '/staff/protocolos', label: 'Protocolos', icon: FileStack },
      { href: '/staff/documentos', label: 'Documentos', icon: FolderTree },
    ],
  },
  {
    title: 'Carteira',
    // Invitations live inside Clients (a tab there), not as a separate entry.
    links: [{ href: '/staff/clientes', label: 'Clientes', icon: Building2 }],
  },
  {
    title: 'Conta',
    links: [
      { href: '/staff/seguranca', label: 'Segurança', icon: ShieldCheck },
      { href: '/staff/novidades', label: 'Novidades', icon: Sparkles },
    ],
  },
];

export const CLIENT_NAVIGATION: NavSection[] = [
  {
    title: 'Acompanhamento',
    links: [
      { href: '/dashboard', label: 'Resumo', icon: LayoutDashboard, nested: false, tour: 'resumo' },
      { href: '/dashboard/protocolos', label: 'Pedidos', icon: FileStack, tour: 'pedidos' },
      { href: '/dashboard/documentos', label: 'Documentos', icon: FolderTree, tour: 'documentos' },
    ],
  },
  {
    title: 'Conta',
    links: [
      { href: '/dashboard/empresa', label: 'Empresa', icon: Users, tour: 'empresa' },
      { href: '/dashboard/seguranca', label: 'Segurança', icon: ShieldCheck, tour: 'seguranca' },
      { href: '/dashboard/novidades', label: 'Novidades', icon: Sparkles },
    ],
  },
];

export const NAVIGATION_BY_AREA = {
  staff: STAFF_NAVIGATION,
  client: CLIENT_NAVIGATION,
} as const;

export type Area = keyof typeof NAVIGATION_BY_AREA;

export function isActive(pathname: string, link: NavLink): boolean {
  if (link.nested === false) return pathname === link.href;
  return pathname === link.href || pathname.startsWith(`${link.href}/`);
}
