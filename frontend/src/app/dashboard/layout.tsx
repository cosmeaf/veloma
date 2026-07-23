import { redirect } from 'next/navigation';

import { SidebarShell } from '@/components/sidebar-shell';
import { ClientTour } from '@/features/onboarding/tour';
import { displayName, getCurrentUser } from '@/lib/auth/session';

export default async function DashboardLayout({ children }: { children: React.ReactNode }) {
  const user = await getCurrentUser();
  if (!user) redirect('/entrar?next=/dashboard');

  return (
    <SidebarShell area="client" userName={displayName(user)} scope="Área de cliente" headerAction={<ClientTour />}>
      {children}
    </SidebarShell>
  );
}
