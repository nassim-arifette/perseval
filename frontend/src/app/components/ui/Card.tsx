'use client';

import { motion, HTMLMotionProps } from 'framer-motion';
import { useTheme } from '@/app/context/ThemeContext';
import { getThemeColors, getThemeShadows } from '@/app/lib/theme';
import { ReactNode } from 'react';

interface CardProps extends HTMLMotionProps<'div'> {
  children: ReactNode;
  hover?: boolean;
  gradient?: string;
  glowing?: boolean;
  padding?: 'none' | 'sm' | 'md' | 'lg';
}

export function Card({
  children,
  hover = true,
  gradient,
  glowing = false,
  padding = 'md',
  className = '',
  ...props
}: CardProps) {
  const { theme } = useTheme();
  const colors = getThemeColors(theme);
  const shadows = getThemeShadows(theme);

  const paddingClasses = {
    none: '',
    sm: 'p-4',
    md: 'p-6',
    lg: 'p-8',
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={hover ? { y: -4, boxShadow: shadows.xl } : undefined}
      transition={{ duration: 0.3 }}
      className={`
        relative rounded-2xl overflow-hidden
        ${paddingClasses[padding]}
        ${className}
      `}
      style={{
        background: gradient || colors.background.card,
        border: `1px solid ${colors.border.default}`,
        boxShadow: shadows.md,
      }}
      {...props}
    >
      {/* Glowing border effect */}
      {glowing && (
        <div
          className="absolute inset-0 rounded-2xl opacity-75 blur-xl"
          style={{
            background: gradient || colors.accent.primary,
            zIndex: -1,
          }}
        />
      )}

      {children}
    </motion.div>
  );
}
