'use client';

import { motion } from 'framer-motion';
import { useTheme } from '@/app/context/ThemeContext';
import { getThemeColors } from '@/app/lib/theme';
import { InputHTMLAttributes, ReactNode, useState } from 'react';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  icon?: ReactNode;
  iconPosition?: 'left' | 'right';
}

export function Input({
  label,
  error,
  icon,
  iconPosition = 'left',
  className = '',
  ...props
}: InputProps) {
  const { theme } = useTheme();
  const colors = getThemeColors(theme);
  const [isFocused, setIsFocused] = useState(false);

  return (
    <div className="w-full">
      {label && (
        <label
          className="block text-sm font-medium mb-2"
          style={{ color: colors.text.secondary }}
        >
          {label}
        </label>
      )}

      <div className="relative">
        {icon && iconPosition === 'left' && (
          <div
            className="absolute left-3 top-1/2 -translate-y-1/2"
            style={{ color: colors.text.tertiary }}
          >
            {icon}
          </div>
        )}

        <input
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          className={`
            w-full px-4 py-2.5 rounded-xl
            transition-all duration-200
            ${icon && iconPosition === 'left' ? 'pl-10' : ''}
            ${icon && iconPosition === 'right' ? 'pr-10' : ''}
            ${className}
          `}
          style={{
            backgroundColor: colors.background.card,
            color: colors.text.primary,
            border: `2px solid ${
              isFocused
                ? colors.border.focus
                : error
                ? colors.accent.danger
                : colors.border.default
            }`,
          }}
          {...props}
        />

        {icon && iconPosition === 'right' && (
          <div
            className="absolute right-3 top-1/2 -translate-y-1/2"
            style={{ color: colors.text.tertiary }}
          >
            {icon}
          </div>
        )}
      </div>

      {error && (
        <motion.p
          initial={{ opacity: 0, y: -5 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-sm mt-1"
          style={{ color: colors.accent.danger }}
        >
          {error}
        </motion.p>
      )}
    </div>
  );
}
