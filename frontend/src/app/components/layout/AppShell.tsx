'use client';

import Link from 'next/link';
import { ReactNode, useEffect, useState } from 'react';
import { Sidebar } from './Sidebar';
import { ThemeToggle } from '../ui/ThemeToggle';
import { useTheme } from '@/app/context/ThemeContext';
import { getThemeColors, theme } from '@/app/lib/theme';

interface AppShellProps {
  children: ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const { theme: currentTheme } = useTheme();
  const colors = getThemeColors(currentTheme);

  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth >= 1024) {
        setIsSidebarOpen(false);
      }
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const toggleSidebar = () => setIsSidebarOpen((prev) => !prev);
  const closeSidebar = () => setIsSidebarOpen(false);

  return (
    <div className="flex min-h-screen" style={{ backgroundColor: colors.background.secondary }}>
      <Sidebar className="hidden lg:flex" />
      <Sidebar
        variant="mobile"
        isOpen={isSidebarOpen}
        onClose={closeSidebar}
        className="lg:hidden"
      />

      {isSidebarOpen && (
        <button
          aria-label="Close menu"
          className="fixed inset-0 z-40 bg-black/40 backdrop-blur-sm lg:hidden"
          onClick={closeSidebar}
        />
      )}

      <div className="flex-1 flex flex-col min-h-screen w-full lg:ml-[240px]">
        <header
          className="lg:hidden sticky top-0 z-30 flex items-center gap-3 px-4 py-3"
          style={{
            backgroundColor: colors.background.card,
            borderBottom: `1px solid ${colors.border.default}`,
          }}
        >
          <button
            onClick={toggleSidebar}
            className="p-2 rounded-xl border"
            style={{
              borderColor: colors.border.default,
              color: colors.text.primary,
            }}
            aria-label="Toggle menu"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.8"
              className="w-5 h-5"
            >
              <path d="M4 6h16M4 12h16M4 18h10" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </button>

          <div className="flex-1 text-center">
            <div
              className="mx-auto mb-1 flex h-10 w-10 items-center justify-center rounded-2xl text-base font-semibold text-white"
              style={{ background: theme.gradients.primary }}
            >
              P
            </div>
            <p className="text-sm font-semibold" style={{ color: colors.text.primary }}>
              Perseval
            </p>
            <p className="text-[11px] uppercase tracking-[0.35em]" style={{ color: colors.text.tertiary }}>
              Trust AI
            </p>
          </div>

          <div className="flex items-center gap-2">
            <Link
              href="/history"
              className="rounded-lg px-3 py-1 text-xs font-medium"
              style={{
                backgroundColor: colors.background.hover,
                color: colors.text.primary,
              }}
            >
              History
            </Link>
            <ThemeToggle />
          </div>
        </header>

        <main className="flex-1 w-full">{children}</main>
      </div>
    </div>
  );
}
