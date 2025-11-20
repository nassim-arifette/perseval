'use client';

import { motion } from 'framer-motion';
import { useTheme } from '@/app/context/ThemeContext';
import { getThemeColors } from '@/app/lib/theme';
import { InputHTMLAttributes, ReactNode, useState } from 'react';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  success?: string;
  helperText?: string;
  icon?: ReactNode;
  iconPosition?: 'left' | 'right';
  showValidation?: boolean;
}

export function Input({
  label,
  error,
  success,
  helperText,
  icon,
  iconPosition = 'left',
  showValidation = false,
  className = '',
  ...props
}: InputProps) {
  const { theme } = useTheme();
  const colors = getThemeColors(theme);
  const [isFocused, setIsFocused] = useState(false);

  const hasError = Boolean(error);
  const hasSuccess = Boolean(success) && !hasError;

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
            ${(icon && iconPosition === 'right') || showValidation ? 'pr-10' : ''}
            ${className}
          `}
          style={{
            backgroundColor: colors.background.card,
            color: colors.text.primary,
            border: `2px solid ${
              isFocused
                ? colors.border.focus
                : hasError
                ? colors.accent.danger
                : hasSuccess
                ? colors.accent.success
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

        {/* Validation Icons */}
        {showValidation && !icon && (
          <div className="absolute right-3 top-1/2 -translate-y-1/2">
            {hasError && (
              <svg className="w-5 h-5 text-rose-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            )}
            {hasSuccess && (
              <svg className="w-5 h-5 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            )}
          </div>
        )}
      </div>

      {/* Helper Text */}
      {helperText && !error && !success && (
        <p
          className="text-xs mt-1"
          style={{ color: colors.text.tertiary }}
        >
          {helperText}
        </p>
      )}

      {/* Error Message */}
      {error && (
        <motion.p
          initial={{ opacity: 0, y: -5 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-xs mt-1 flex items-center gap-1"
          style={{ color: colors.accent.danger }}
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          {error}
        </motion.p>
      )}

      {/* Success Message */}
      {success && (
        <motion.p
          initial={{ opacity: 0, y: -5 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-xs mt-1 flex items-center gap-1"
          style={{ color: colors.accent.success }}
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          {success}
        </motion.p>
      )}
    </div>
  );
}
