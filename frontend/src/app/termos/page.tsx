import type { Metadata } from 'next';

import { LegalArticle } from '@/components/legal-article';
import { termos } from '@/content/legal';

export const metadata: Metadata = {
  title: termos.title,
  description: termos.summary,
  alternates: { canonical: '/termos' },
};

export default function TermosPage() {
  return <LegalArticle doc={termos} />;
}
