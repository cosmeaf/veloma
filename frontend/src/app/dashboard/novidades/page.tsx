import type { Metadata } from 'next';

import { PageHeader } from '@/components/ui';
import { APP_VERSION } from '@/content/changelog';
import { ChangelogView } from '@/features/changelog/changelog-view';

export const metadata: Metadata = { title: 'Novidades' };

export default function ClientChangelogPage() {
  return (
    <>
      <PageHeader title="Novidades e correções" description={`O que mudou na plataforma. Versão atual: v${APP_VERSION}.`} />
      <ChangelogView />
    </>
  );
}
