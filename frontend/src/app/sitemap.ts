import type { MetadataRoute } from 'next';

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://veloma.app';

export default function sitemap(): MetadataRoute.Sitemap {
  const routes = ['', '/termos', '/privacidade', '/cookies'];
  return routes.map((path) => ({
    url: `${SITE_URL}${path}`,
    changeFrequency: path === '' ? 'monthly' : 'yearly',
    priority: path === '' ? 1 : 0.5,
  }));
}
