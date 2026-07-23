import type { MetadataRoute } from 'next';

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://veloma.app';

export default function robots(): MetadataRoute.Robots {
  return {
    rules: {
      userAgent: '*',
      allow: '/',
      // Client/staff areas and API are private — keep them out of the index.
      disallow: ['/staff', '/dashboard', '/api', '/primeiro-acesso', '/entrar', '/recuperar', '/convite'],
    },
    sitemap: `${SITE_URL}/sitemap.xml`,
  };
}
