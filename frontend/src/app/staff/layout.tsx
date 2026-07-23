import { redirect } from 'next/navigation';

import { SidebarShell } from '@/components/sidebar-shell';
import { displayName, getCurrentUser, isStaff } from '@/lib/auth/session';

export default async function StaffLayout({ children }: { children: React.ReactNode }) {
  const user = await getCurrentUser();
  if (!user) redirect('/entrar?next=/staff');
  if (user.must_change_credentials) redirect('/primeiro-acesso');
  if (!isStaff(user)) redirect('/dashboard');

  return (
    <SidebarShell area="staff" userName={displayName(user)} scope="Equipa">
      {children}
    </SidebarShell>
  );
}
