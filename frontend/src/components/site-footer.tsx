import { Clock, Mail, MapPin, Phone } from 'lucide-react';
import Link from 'next/link';
import type { SVGProps } from 'react';

import { VelomaMark } from '@/components/brand';
import { site } from '@/content/site';

// Brand glyphs (lucide dropped brand icons); simple-icons style paths.
function Facebook(props: SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden {...props}>
      <path d="M24 12.07C24 5.4 18.63 0 12 0S0 5.4 0 12.07C0 18.1 4.39 23.1 10.13 24v-8.44H7.08v-3.49h3.05V9.41c0-3.02 1.79-4.69 4.53-4.69 1.31 0 2.68.24 2.68.24v2.97h-1.51c-1.49 0-1.96.93-1.96 1.89v2.25h3.33l-.53 3.49h-2.8V24C19.61 23.1 24 18.1 24 12.07z" />
    </svg>
  );
}
function Instagram(props: SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden {...props}>
      <path d="M12 2.16c3.2 0 3.58.01 4.85.07 1.17.05 1.8.25 2.23.41.56.22.96.48 1.38.9.42.42.68.82.9 1.38.16.42.36 1.06.41 2.23.06 1.27.07 1.65.07 4.85s-.01 3.58-.07 4.85c-.05 1.17-.25 1.8-.41 2.23-.22.56-.48.96-.9 1.38-.42.42-.82.68-1.38.9-.42.16-1.06.36-2.23.41-1.27.06-1.65.07-4.85.07s-3.58-.01-4.85-.07c-1.17-.05-1.8-.25-2.23-.41a3.7 3.7 0 01-1.38-.9 3.7 3.7 0 01-.9-1.38c-.16-.42-.36-1.06-.41-2.23-.06-1.27-.07-1.65-.07-4.85s.01-3.58.07-4.85c.05-1.17.25-1.8.41-2.23.22-.56.48-.96.9-1.38.42-.42.82-.68 1.38-.9.42-.16 1.06-.36 2.23-.41C8.42 2.17 8.8 2.16 12 2.16zM12 0C8.74 0 8.33.01 7.05.07 5.78.13 4.9.33 4.14.63c-.79.31-1.46.72-2.12 1.38C1.35 2.67.94 3.34.63 4.14.33 4.9.13 5.78.07 7.05.01 8.33 0 8.74 0 12s.01 3.67.07 4.95c.06 1.27.26 2.15.56 2.91.31.8.72 1.47 1.38 2.13.66.66 1.33 1.07 2.12 1.38.76.3 1.64.5 2.91.56C8.33 23.99 8.74 24 12 24s3.67-.01 4.95-.07c1.27-.06 2.15-.26 2.91-.56.8-.31 1.47-.72 2.13-1.38.66-.66 1.07-1.33 1.38-2.13.3-.76.5-1.64.56-2.91.06-1.28.07-1.69.07-4.95s-.01-3.67-.07-4.95c-.06-1.27-.26-2.15-.56-2.91a5.86 5.86 0 00-1.38-2.13A5.86 5.86 0 0019.86.63c-.76-.3-1.64-.5-2.91-.56C15.67.01 15.26 0 12 0zm0 5.84a6.16 6.16 0 100 12.32A6.16 6.16 0 0012 5.84zm0 10.16a4 4 0 110-8 4 4 0 010 8zm7.85-10.4a1.44 1.44 0 11-2.88 0 1.44 1.44 0 012.88 0z" />
    </svg>
  );
}
function Linkedin(props: SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden {...props}>
      <path d="M20.45 20.45h-3.56v-5.57c0-1.33-.02-3.04-1.85-3.04-1.85 0-2.14 1.45-2.14 2.94v5.67H9.35V9h3.41v1.56h.05c.48-.9 1.63-1.85 3.36-1.85 3.6 0 4.27 2.37 4.27 5.45v6.29zM5.34 7.43a2.06 2.06 0 110-4.13 2.06 2.06 0 010 4.13zm1.78 13.02H3.55V9h3.57v11.45zM22.22 0H1.77C.8 0 0 .77 0 1.72v20.56C0 23.23.8 24 1.77 24h20.45c.98 0 1.78-.77 1.78-1.72V1.72C24 .77 23.2 0 22.22 0z" />
    </svg>
  );
}

const LEGAL_LINKS = [
  { href: '/termos', label: 'Termos e Condições' },
  { href: '/privacidade', label: 'Política de Privacidade' },
  { href: '/cookies', label: 'Política de Cookies' },
];

const SOCIAL = [
  { href: site.social.facebook, label: 'Facebook', Icon: Facebook },
  { href: site.social.instagram, label: 'Instagram', Icon: Instagram },
  { href: site.social.linkedin, label: 'LinkedIn', Icon: Linkedin },
];

export function SiteFooter() {
  const year = new Date().getFullYear();

  return (
    <footer className="bg-navy text-ivory/70">
      <div className="mx-auto max-w-6xl px-6 py-12">
        <div className="grid gap-10 md:grid-cols-3">
          {/* Marca + redes sociais. */}
          <div>
            <VelomaMark tone="dark" />
            <p className="mt-3 max-w-xs text-sm">Contabilidade e Consultoria Fiscal. A sua contabilidade, agora digital.</p>
            <div className="mt-4 flex items-center gap-2">
              {SOCIAL.map(({ href, label, Icon }) => (
                <a
                  key={label}
                  href={href}
                  target="_blank"
                  rel="noreferrer noopener"
                  aria-label={label}
                  className="hover:bg-white/10 hover:text-ivory inline-flex size-9 items-center justify-center rounded-lg border border-white/15 transition-colors"
                >
                  <Icon className="size-4.5" aria-hidden />
                </a>
              ))}
            </div>
          </div>

          {/* Contactos. */}
          <div>
            <h2 className="text-ivory text-sm font-semibold">Contactos</h2>
            <ul className="mt-4 space-y-3 text-sm">
              <li className="flex items-start gap-2.5">
                <MapPin className="text-gold-high mt-0.5 size-4 shrink-0" aria-hidden />
                <span>{site.address}</span>
              </li>
              <li className="flex items-start gap-2.5">
                <Phone className="text-gold-high mt-0.5 size-4 shrink-0" aria-hidden />
                <span>{site.phones.join(' · ')}</span>
              </li>
              <li className="flex items-start gap-2.5">
                <Mail className="text-gold-high mt-0.5 size-4 shrink-0" aria-hidden />
                <a href={`mailto:${site.email}`} className="hover:text-ivory">
                  {site.email}
                </a>
              </li>
              <li className="flex items-start gap-2.5">
                <Clock className="text-gold-high mt-0.5 size-4 shrink-0" aria-hidden />
                <span>{site.hours}</span>
              </li>
            </ul>
          </div>

          {/* Legal. */}
          <div>
            <h2 className="text-ivory text-sm font-semibold">Legal</h2>
            <ul className="mt-4 space-y-2.5 text-sm">
              {LEGAL_LINKS.map((link) => (
                <li key={link.href}>
                  <Link href={link.href} className="hover:text-ivory">
                    {link.label}
                  </Link>
                </li>
              ))}
              <li>
                <Link href="/entrar" className="hover:text-ivory">
                  Área de cliente
                </Link>
              </li>
            </ul>
          </div>
        </div>

        <div className="mt-10 flex flex-wrap items-center justify-between gap-2 border-t border-white/10 pt-6 text-xs text-ivory/55">
          <span>© {year} Veloma — Contabilidade e Consultoria Fiscal, Lda. Todos os direitos reservados.</span>
          <span>Tratamento de dados em conformidade com o RGPD (UE 2016/679).</span>
        </div>
      </div>
    </footer>
  );
}
