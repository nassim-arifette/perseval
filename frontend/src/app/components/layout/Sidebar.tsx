'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { useTheme } from '@/app/context/ThemeContext';
import { getThemeColors, getThemeShadows, theme } from '@/app/lib/theme';
import { ThemeToggle } from '../ui/ThemeToggle';
import { usePathname } from 'next/navigation';
import Link from 'next/link';
import { useState, ReactNode } from 'react';

interface NavItem {
  name: string;
  path: string;
  icon: ReactNode;
  badge?: number;
}

const navItems: NavItem[] = [
  {
    name: 'Checker',
    path: '/',
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-5 h-5">
        <path fillRule="evenodd" d="M8.485 2.495c.673-1.167 2.357-1.167 3.03 0l6.28 10.875c.673 1.167-.17 2.625-1.516 2.625H3.72c-1.347 0-2.189-1.458-1.515-2.625L8.485 2.495zM10 5a.75.75 0 01.75.75v3.5a.75.75 0 01-1.5 0v-3.5A.75.75 0 0110 5zm0 9a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" />
      </svg>
    ),
  },
  {
    name: 'Marketplace',
    path: '/marketplace',
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-5 h-5">
        <path fillRule="evenodd" d="M6 3.75A2.75 2.75 0 018.75 1h2.5A2.75 2.75 0 0114 3.75v.443c.572.055 1.14.122 1.706.2C17.053 4.582 18 5.75 18 7.07V19a1 1 0 01-1 1H3a1 1 0 01-1-1V7.07c0-1.32.947-2.489 2.294-2.676A41.047 41.047 0 016 4.193V3.75zm1.5 0V4.09c.504-.034 1.011-.065 1.521-.091V3.75c0-.69-.56-1.25-1.25-1.25h-2.5c-.69 0-1.25.56-1.25 1.25v.25c.51.026 1.017.057 1.521.091V3.75zM5 8.07l.01-.012a.75.75 0 011.06.012l1.93 1.93a.75.75 0 01-1.06 1.06L5 9.13V8.07zm10 0v1.06l-1.94 1.94a.75.75 0 11-1.06-1.06l1.93-1.93a.75.75 0 011.06-.012l.01.012zM10 7a1 1 0 100 2 1 1 0 000-2z" clipRule="evenodd" />
      </svg>
    ),
  },
  {
    name: 'Dashboard',
    path: '/dashboard',
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-5 h-5">
        <path d="M10 2a.75.75 0 01.75.75v1.5a.75.75 0 01-1.5 0v-1.5A.75.75 0 0110 2zM10 15a.75.75 0 01.75.75v1.5a.75.75 0 01-1.5 0v-1.5A.75.75 0 0110 15zM10 7a3 3 0 100 6 3 3 0 000-6zM15.657 5.404a.75.75 0 10-1.06-1.06l-1.061 1.06a.75.75 0 001.06 1.06l1.06-1.06zM6.464 14.596a.75.75 0 10-1.06-1.06l-1.06 1.06a.75.75 0 001.06 1.06l1.06-1.06zM18 10a.75.75 0 01-.75.75h-1.5a.75.75 0 010-1.5h1.5A.75.75 0 0118 10zM5 10a.75.75 0 01-.75.75h-1.5a.75.75 0 010-1.5h1.5A.75.75 0 015 10zM14.596 15.657a.75.75 0 001.06-1.06l-1.06-1.061a.75.75 0 10-1.06 1.06l1.06 1.06zM5.404 6.464a.75.75 0 001.06-1.06l-1.06-1.06a.75.75 0 10-1.061 1.06l1.06 1.06z" />
      </svg>
    ),
  },
  {
    name: 'History',
    path: '/history',
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-5 h-5">
        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm.75-13a.75.75 0 00-1.5 0v5c0 .414.336.75.75.75h4a.75.75 0 000-1.5h-3.25V5z" clipRule="evenodd" />
      </svg>
    ),
  },
];

export function Sidebar() {
  const { theme: currentTheme } = useTheme();
  const colors = getThemeColors(currentTheme);
  const shadows = getThemeShadows(currentTheme);
  const pathname = usePathname();
  const [isCollapsed, setIsCollapsed] = useState(false);

  return (
    <motion.aside
      initial={{ x: -300 }}
      animate={{ x: 0, width: isCollapsed ? '80px' : '240px' }}
      transition={{ duration: 0.3 }}
      className="fixed left-0 top-0 h-screen z-50 flex flex-col"
      style={{
        backgroundColor: colors.background.card,
        borderRight: `1px solid ${colors.border.default}`,
        boxShadow: shadows.lg,
      }}
    >
      {/* Logo Section */}
      <div className="p-6 flex items-center justify-between">
        <motion.div
          animate={{ opacity: isCollapsed ? 0 : 1 }}
          className="flex items-center gap-3"
        >
          <div
            className="w-10 h-10 rounded-xl flex items-center justify-center text-white font-bold text-lg"
            style={{
              background: theme.gradients.primary,
            }}
          >
            P
          </div>
          {!isCollapsed && (
            <motion.h1
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="text-xl font-bold bg-gradient-to-r from-indigo-500 to-purple-600 bg-clip-text text-transparent"
            >
              Perseval
            </motion.h1>
          )}
        </motion.div>

        {/* Collapse button */}
        <motion.button
          onClick={() => setIsCollapsed(!isCollapsed)}
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.9 }}
          className="p-2 rounded-lg"
          style={{
            color: colors.text.tertiary,
            backgroundColor: colors.background.hover,
          }}
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 20 20"
            fill="currentColor"
            className="w-4 h-4"
            style={{
              transform: isCollapsed ? 'rotate(180deg)' : 'rotate(0deg)',
              transition: 'transform 0.3s',
            }}
          >
            <path
              fillRule="evenodd"
              d="M12.79 5.23a.75.75 0 01-.02 1.06L8.832 10l3.938 3.71a.75.75 0 11-1.04 1.08l-4.5-4.25a.75.75 0 010-1.08l4.5-4.25a.75.75 0 011.06.02z"
              clipRule="evenodd"
            />
          </svg>
        </motion.button>
      </div>

      {/* Navigation Items */}
      <nav className="flex-1 px-3">
        <AnimatePresence>
          {navItems.map((item, index) => {
            const isActive = pathname === item.path;
            return (
              <Link key={item.path} href={item.path}>
                <motion.div
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.1 }}
                  whileHover={{ x: 4 }}
                  className="mb-2 relative"
                >
                  <motion.div
                    className="flex items-center gap-3 px-4 py-3 rounded-xl cursor-pointer transition-all duration-200"
                    style={{
                      backgroundColor: isActive
                        ? `${colors.accent.primary}15`
                        : 'transparent',
                      color: isActive ? colors.accent.primary : colors.text.secondary,
                    }}
                    whileHover={{
                      backgroundColor: isActive
                        ? `${colors.accent.primary}20`
                        : colors.background.hover,
                    }}
                  >
                    {/* Active indicator */}
                    {isActive && (
                      <motion.div
                        layoutId="activeTab"
                        className="absolute left-0 w-1 h-8 rounded-r-full"
                        style={{ background: theme.gradients.primary }}
                        transition={{ type: 'spring', stiffness: 300, damping: 30 }}
                      />
                    )}

                    <div className="flex-shrink-0">{item.icon}</div>

                    {!isCollapsed && (
                      <motion.span
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className="font-medium"
                      >
                        {item.name}
                      </motion.span>
                    )}

                    {item.badge && !isCollapsed && (
                      <motion.span
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        className="ml-auto px-2 py-0.5 rounded-full text-xs font-semibold"
                        style={{
                          backgroundColor: colors.accent.danger,
                          color: colors.text.inverse,
                        }}
                      >
                        {item.badge}
                      </motion.span>
                    )}
                  </motion.div>
                </motion.div>
              </Link>
            );
          })}
        </AnimatePresence>
      </nav>

      {/* Footer with theme toggle */}
      <div className="p-4 border-t" style={{ borderColor: colors.border.default }}>
        <div className={`flex items-center ${isCollapsed ? 'justify-center' : 'justify-between'}`}>
          {!isCollapsed && (
            <span className="text-sm" style={{ color: colors.text.tertiary }}>
              Theme
            </span>
          )}
          <ThemeToggle />
        </div>
      </div>
    </motion.aside>
  );
}
