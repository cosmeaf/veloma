'use client';

import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from 'react';

type Theme = 'light' | 'dark';

type ThemeApi = {
  theme: Theme;
  soundEnabled: boolean;
  setTheme: (theme: Theme) => void;
  setSoundEnabled: (enabled: boolean) => void;
  playSound: () => void;
};

const ThemeContext = createContext<ThemeApi | null>(null);

/**
 * Applies and persists the user's theme and sound preference.
 *
 * Initial values come from the server (per-user, follows devices); changes are
 * written back through the BFF and mirrored on the document root immediately.
 */
export function ThemeProvider({
  initialTheme,
  initialSound,
  children,
}: {
  initialTheme: Theme;
  initialSound: boolean;
  children: ReactNode;
}) {
  const [theme, setThemeState] = useState<Theme>(initialTheme);
  const [soundEnabled, setSoundState] = useState<boolean>(initialSound);

  const persist = useCallback((body: Record<string, unknown>) => {
    void fetch('/api/auth/preferences', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
  }, []);

  const setTheme = useCallback(
    (next: Theme) => {
      setThemeState(next);
      persist({ theme: next });
    },
    [persist],
  );

  const setSoundEnabled = useCallback(
    (next: boolean) => {
      setSoundState(next);
      persist({ sound_enabled: next });
    },
    [persist],
  );

  const playSound = useCallback(() => {
    if (!soundEnabled) return;
    try {
      const ctx = new (window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext)();
      const oscillator = ctx.createOscillator();
      const gain = ctx.createGain();
      oscillator.connect(gain);
      gain.connect(ctx.destination);
      // A clearer, louder two-note chime (was a faint single beep at 0.05).
      oscillator.type = 'sine';
      oscillator.frequency.setValueAtTime(660, ctx.currentTime);
      oscillator.frequency.setValueAtTime(990, ctx.currentTime + 0.12);
      gain.gain.setValueAtTime(0.0001, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.3, ctx.currentTime + 0.02);
      gain.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + 0.4);
      oscillator.start();
      oscillator.stop(ctx.currentTime + 0.4);
    } catch {
      // Autoplay policies may block this; silence is acceptable.
    }
  }, [soundEnabled]);

  return (
    <ThemeContext.Provider value={{ theme, soundEnabled, setTheme, setSoundEnabled, playSound }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme(): ThemeApi {
  const context = useContext(ThemeContext);
  if (!context) {
    return {
      theme: 'light',
      soundEnabled: true,
      setTheme: () => {},
      setSoundEnabled: () => {},
      playSound: () => {},
    };
  }
  return context;
}
