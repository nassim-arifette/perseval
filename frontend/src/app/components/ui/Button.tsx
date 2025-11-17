'use client';

import { motion, HTMLMotionProps } from 'framer-motion';
import { useTheme } from '@/app/context/ThemeContext';
import { getThemeColors, theme } from '@/app/lib/theme';
import { ReactNode } from 'react';

export type ButtonVariant = 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger' | 'success';
export type ButtonSize = 'sm' | 'md' | 'lg';

interface ButtonProps extends Omit<HTMLMotionProps<'button'>, 'children'> {
  children: ReactNode;
  variant?: ButtonVariant;
  size?: ButtonSize;
  fullWidth?: boolean;
  loading?: boolean;
  icon?: ReactNode;
  iconPosition?: 'left' | 'right';
  gradient?: boolean;
}

export function Button({
  children,
  variant = 'primary',
  size = 'md',
  fullWidth = false,
  loading = false,
  icon,
  iconPosition = 'left',
  gradient = false,
  disabled,
  className = '',
  ...props
}: ButtonProps) {
  const { theme: currentTheme } = useTheme();
  const colors = getThemeColors(currentTheme);

  const sizeClasses = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-base',
    lg: 'px-6 py-3 text-lg',
  };

  const getVariantStyles = () => {
    switch (variant) {
      case 'primary':
        if (gradient) {
          return {
            background: theme.gradients.primary,
            color: colors.text.inverse,
            border: 'none',
          };
        }
        return {
          backgroundColor: colors.accent.primary,
          color: colors.text.inverse,
          border: 'none',
        };
      case 'secondary':
        if (gradient) {
          return {
            background: theme.gradients.secondary,
            color: colors.text.inverse,
            border: 'none',
          };
        }
        return {
          backgroundColor: colors.accent.secondary,
          color: colors.text.inverse,
          border: 'none',
        };
      case 'outline':
        return {
          backgroundColor: 'transparent',
          color: colors.accent.primary,
          border: `2px solid ${colors.accent.primary}`,
        };
      case 'ghost':
        return {
          backgroundColor: 'transparent',
          color: colors.text.primary,
          border: 'none',
        };
      case 'danger':
        return {
          backgroundColor: colors.accent.danger,
          color: colors.text.inverse,
          border: 'none',
        };
      case 'success':
        if (gradient) {
          return {
            background: theme.gradients.success,
            color: colors.text.inverse,
            border: 'none',
          };
        }
        return {
          backgroundColor: colors.accent.success,
          color: colors.text.inverse,
          border: 'none',
        };
    }
  };

  const variantStyles = getVariantStyles();

  return (
    <motion.button
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      disabled={disabled || loading}
      className={`
        relative overflow-hidden font-medium rounded-xl
        transition-all duration-300 ease-out
        disabled:opacity-50 disabled:cursor-not-allowed
        flex items-center justify-center gap-2
        ${sizeClasses[size]}
        ${fullWidth ? 'w-full' : ''}
        ${className}
      `}
      style={{
        ...variantStyles,
        boxShadow: disabled || loading ? 'none' : theme.shadows[currentTheme].md,
      }}
      {...props}
    >
      {/* Shimmer effect on hover */}
      <motion.div
        className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent"
        initial={{ x: '-100%' }}
        whileHover={{ x: '100%' }}
        transition={{ duration: 0.6, ease: 'easeInOut' }}
      />

      {/* Content */}
      <span className="relative flex items-center gap-2">
        {loading ? (
          <svg
            className="animate-spin h-5 w-5"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
        ) : (
          <>
            {icon && iconPosition === 'left' && icon}
            {children}
            {icon && iconPosition === 'right' && icon}
          </>
        )}
      </span>
    </motion.button>
  );
}
