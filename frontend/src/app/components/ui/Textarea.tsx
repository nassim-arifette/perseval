'use client';

import { motion } from 'framer-motion';
import { useTheme } from '@/app/context/ThemeContext';
import { getThemeColors } from '@/app/lib/theme';
import { TextareaHTMLAttributes, useState } from 'react';

interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
  showCount?: boolean;
  maxCount?: number;
}

export function Textarea({
  label,
  error,
  showCount = false,
  maxCount,
  value,
  className = '',
  ...props
}: TextareaProps) {
  const { theme } = useTheme();
  const colors = getThemeColors(theme);
  const [isFocused, setIsFocused] = useState(false);

  const currentLength = typeof value === 'string' ? value.length : 0;

  return (
    <div className="w-full">
      {label && (
        <div className="flex justify-between items-center mb-2">
          <label
            className="block text-sm font-medium"
            style={{ color: colors.text.secondary }}
          >
            {label}
          </label>
          {showCount && maxCount && (
            <span
              className="text-xs"
              style={{
                color:
                  currentLength > maxCount
                    ? colors.accent.danger
                    : colors.text.tertiary,
              }}
            >
              {currentLength} / {maxCount}
            </span>
          )}
        </div>
      )}

      <textarea
        onFocus={() => setIsFocused(true)}
        onBlur={() => setIsFocused(false)}
        value={value}
        className={`
          w-full px-4 py-3 rounded-xl
          transition-all duration-200
          resize-none
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
