import Link from 'next/link';

import { SiteFooter } from '@/components/site-footer';
import { SiteHeader } from '@/components/site-header';
import { legalDocuments, legalUpdatedAt, type LegalDocument } from '@/content/legal';

export function LegalArticle({ doc }: { doc: LegalDocument }) {
  return (
    <>
      <SiteHeader />
      <main className="mx-auto w-full max-w-3xl flex-1 px-6 py-14">
        <p className="text-gold-sun text-sm font-medium">Legal</p>
        <h1 className="font-display text-navy mt-2 text-3xl font-semibold tracking-tight">{doc.title}</h1>
        <p className="text-navy/60 mt-2 text-sm">{doc.summary}</p>
        <p className="text-navy/45 mt-1 text-xs">Última atualização: {legalUpdatedAt}</p>

        <div className="mt-10 space-y-8">
          {doc.sections.map((section) => (
            <section key={section.heading}>
              <h2 className="text-navy text-base font-semibold">{section.heading}</h2>
              <div className="mt-2 space-y-2">
                {section.paragraphs.map((paragraph, index) => (
                  <p key={index} className="text-navy/75 text-sm leading-relaxed">
                    {paragraph}
                  </p>
                ))}
              </div>
            </section>
          ))}
        </div>

        <nav className="border-mist mt-12 flex flex-wrap gap-4 border-t pt-6 text-sm">
          {legalDocuments
            .filter((other) => other.slug !== doc.slug)
            .map((other) => (
              <Link key={other.slug} href={`/${other.slug}`} className="text-navy hover:underline">
                {other.title}
              </Link>
            ))}
        </nav>
      </main>
      <SiteFooter />
    </>
  );
}
