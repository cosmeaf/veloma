import type { Metadata, Viewport } from 'next';
import { Cinzel, Jost } from 'next/font/google';

import { site } from '@/content/site';

import './globals.css';

// Cinzel for institutional headings, Jost for interface text, per the manual.
const cinzel = Cinzel({ subsets: ['latin'], weight: ['400', '600'], variable: '--font-cinzel', display: 'swap' });
const jost = Jost({ subsets: ['latin'], weight: ['300', '400', '500', '600'], variable: '--font-jost', display: 'swap' });

export const metadata: Metadata = {
  title: {
    default: `${site.name} — ${site.tagline}`,
    template: `%s · ${site.name}`,
  },
  description: site.description,
  icons: { icon: '/favicon.ico' },
};

export const viewport: Viewport = {
  themeColor: '#20193B',
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="pt-PT" className={`${cinzel.variable} ${jost.variable} h-full antialiased`}>
      <body className="bg-mist/30 text-navy flex min-h-full flex-col">{children}</body>
    </html>
  );
}
