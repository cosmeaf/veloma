import type { Metadata } from 'next';

import { LegalArticle } from '@/components/legal-article';
import { cookies } from '@/content/legal';

export const metadata: Metadata = {
  title: cookies.title,
  description: cookies.summary,
  alternates: { canonical: '/cookies' },
};

export default function CookiesPage() {
  return <LegalArticle doc={cookies} />;
}
