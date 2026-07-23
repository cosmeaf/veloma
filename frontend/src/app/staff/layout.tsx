import { redirect } from 'next/navigation';

import { SidebarShell } from '@/components/sidebar-shell';
import { ThemeProvider } from '@/components/theme-provider';
import { ToastProvider } from '@/components/toast';
import { displayName, getCurrentUser, isStaff } from '@/lib/auth/session';

export default async function StaffLayout({ children }: { children: React.ReactNode }) {
  const user = await getCurrentUser();
  if (!user) redirect('/entrar?next=/staff');
  if (user.must_change_credentials) redirect('/primeiro-acesso');
  if (!isStaff(user)) redirect('/dashboard');

  const prefs = user.preferences ?? { theme: 'light' as const, sound_enabled: true };

  return (
    <ThemeProvider initialTheme={prefs.theme} initialSound={prefs.sound_enabled}>
      <ToastProvider>
        <SidebarShell area="staff" userName={displayName(user)} scope="Equipa">
          {children}
        </SidebarShell>
      </ToastProvider>
    </ThemeProvider>
  );
}
