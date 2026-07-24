import type { Metadata, Viewport } from 'next';
import { Cinzel, Jost } from 'next/font/google';

import { CookieConsent } from '@/components/cookie-consent';
import { site } from '@/content/site';

import './globals.css';

// Cinzel for institutional headings, Jost for interface text, per the manual.
const cinzel = Cinzel({ subsets: ['latin'], weight: ['400', '600'], variable: '--font-cinzel', display: 'swap' });
const jost = Jost({ subsets: ['latin'], weight: ['300', '400', '500', '600'], variable: '--font-jost', display: 'swap' });

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://veloma.app';

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: {
    default: `${site.name} — ${site.tagline}`,
    template: `%s · ${site.name}`,
  },
  description: site.description,
  applicationName: site.product,
  keywords: [
    'contabilidade',
    'contabilidade online',
    'consultoria fiscal',
    'gestão de documentos',
    'digitalização',
    'Veloma',
    'Veloma Digital',
  ],
  authors: [{ name: 'Veloma' }],
  icons: { icon: '/favicon.ico' },
  alternates: { canonical: '/' },
  robots: { index: true, follow: true },
  openGraph: {
    type: 'website',
    locale: 'pt_PT',
    url: SITE_URL,
    siteName: site.name,
    title: `${site.name} — ${site.tagline}`,
    description: site.description,
  },
  twitter: {
    card: 'summary_large_image',
    title: `${site.name} — ${site.tagline}`,
    description: site.description,
  },
};

export const viewport: Viewport = {
  themeColor: '#20193B',
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="pt-PT" className={`${cinzel.variable} ${jost.variable} h-full antialiased`}>
      <body className="bg-mist/30 text-navy flex min-h-full flex-col">
        {children}
        <CookieConsent />
      </body>
    </html>
  );
}
