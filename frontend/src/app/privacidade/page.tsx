import type { Metadata } from 'next';

import { LegalArticle } from '@/components/legal-article';
import { privacidade } from '@/content/legal';

export const metadata: Metadata = {
  title: privacidade.title,
  description: privacidade.summary,
  alternates: { canonical: '/privacidade' },
};

export default function PrivacidadePage() {
  return <LegalArticle doc={privacidade} />;
}
