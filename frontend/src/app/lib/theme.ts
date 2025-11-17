// Modern Design System for Perseval
// Minimalist base with vibrant gradients and bold colors

export type ThemeMode = 'light' | 'dark';

export const theme = {
  colors: {
    light: {
      // Base colors
      background: {
        primary: '#FFFFFF',
        secondary: '#F8FAFC',
        tertiary: '#F1F5F9',
        card: '#FFFFFF',
        hover: '#F8FAFC',
      },
      text: {
        primary: '#0F172A',
        secondary: '#475569',
        tertiary: '#94A3B8',
        inverse: '#FFFFFF',
      },
      border: {
        default: '#E2E8F0',
        hover: '#CBD5E1',
        focus: '#3B82F6',
      },
      // Vibrant accent colors
      accent: {
        primary: '#6366F1', // Indigo
        secondary: '#8B5CF6', // Purple
        tertiary: '#EC4899', // Pink
        success: '#10B981', // Emerald
        warning: '#F59E0B', // Amber
        danger: '#EF4444', // Red
        info: '#3B82F6', // Blue
      },
      // Risk-specific colors
      risk: {
        high: {
          bg: '#FEE2E2',
          border: '#FCA5A5',
          text: '#991B1B',
          accent: '#EF4444',
        },
        medium: {
          bg: '#FEF3C7',
          border: '#FCD34D',
          text: '#92400E',
          accent: '#F59E0B',
        },
        low: {
          bg: '#D1FAE5',
          border: '#6EE7B7',
          text: '#065F46',
          accent: '#10B981',
        },
      },
    },
    dark: {
      // Base colors
      background: {
        primary: '#0F172A',
        secondary: '#1E293B',
        tertiary: '#334155',
        card: '#1E293B',
        hover: '#334155',
      },
      text: {
        primary: '#F8FAFC',
        secondary: '#CBD5E1',
        tertiary: '#64748B',
        inverse: '#0F172A',
      },
      border: {
        default: '#334155',
        hover: '#475569',
        focus: '#3B82F6',
      },
      // Vibrant accent colors (same as light for consistency)
      accent: {
        primary: '#818CF8', // Lighter indigo
        secondary: '#A78BFA', // Lighter purple
        tertiary: '#F472B6', // Lighter pink
        success: '#34D399', // Lighter emerald
        warning: '#FBBF24', // Lighter amber
        danger: '#F87171', // Lighter red
        info: '#60A5FA', // Lighter blue
      },
      // Risk-specific colors
      risk: {
        high: {
          bg: '#7F1D1D',
          border: '#991B1B',
          text: '#FECACA',
          accent: '#F87171',
        },
        medium: {
          bg: '#78350F',
          border: '#92400E',
          text: '#FDE68A',
          accent: '#FBBF24',
        },
        low: {
          bg: '#064E3B',
          border: '#065F46',
          text: '#A7F3D0',
          accent: '#34D399',
        },
      },
    },
  },

  // Vibrant gradients
  gradients: {
    primary: 'linear-gradient(135deg, #667EEA 0%, #764BA2 100%)',
    secondary: 'linear-gradient(135deg, #F093FB 0%, #F5576C 100%)',
    success: 'linear-gradient(135deg, #0BA360 0%, #3CBA92 100%)',
    info: 'linear-gradient(135deg, #4FACFE 0%, #00F2FE 100%)',
    warning: 'linear-gradient(135deg, #FA709A 0%, #FEE140 100%)',
    danger: 'linear-gradient(135deg, #FF6B6B 0%, #FFE66D 100%)',
    sunset: 'linear-gradient(135deg, #FA8BFF 0%, #2BD2FF 50%, #2BFF88 100%)',
    ocean: 'linear-gradient(135deg, #2E3192 0%, #1BFFFF 100%)',
    fire: 'linear-gradient(135deg, #FF6B6B 0%, #FFE66D 100%)',
    cool: 'linear-gradient(135deg, #A8EDEA 0%, #FED6E3 100%)',
    royal: 'linear-gradient(135deg, #667EEA 0%, #F857A6 100%)',
    aurora: 'linear-gradient(135deg, #A8EDEA 0%, #FAD0C4 100%)',
  },

  // Animated gradient backgrounds
  animatedGradients: {
    rainbow: 'linear-gradient(45deg, #FF6B6B, #4ECDC4, #45B7D1, #F7DC6F, #FF6B6B)',
    cosmic: 'linear-gradient(45deg, #667EEA, #764BA2, #F093FB, #667EEA)',
    sunset: 'linear-gradient(45deg, #FA709A, #FEE140, #FA8BFF, #FA709A)',
  },

  // Spacing scale
  spacing: {
    xs: '0.25rem',   // 4px
    sm: '0.5rem',    // 8px
    md: '1rem',      // 16px
    lg: '1.5rem',    // 24px
    xl: '2rem',      // 32px
    '2xl': '3rem',   // 48px
    '3xl': '4rem',   // 64px
    '4xl': '6rem',   // 96px
  },

  // Border radius
  radius: {
    none: '0',
    sm: '0.375rem',  // 6px
    md: '0.5rem',    // 8px
    lg: '0.75rem',   // 12px
    xl: '1rem',      // 16px
    '2xl': '1.5rem', // 24px
    '3xl': '2rem',   // 32px
    full: '9999px',
  },

  // Shadows
  shadows: {
    light: {
      sm: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
      md: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
      lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
      xl: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
      '2xl': '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
      glow: '0 0 20px rgba(99, 102, 241, 0.3)',
      glowPink: '0 0 20px rgba(236, 72, 153, 0.3)',
      glowGreen: '0 0 20px rgba(16, 185, 129, 0.3)',
    },
    dark: {
      sm: '0 1px 2px 0 rgba(0, 0, 0, 0.3)',
      md: '0 4px 6px -1px rgba(0, 0, 0, 0.4), 0 2px 4px -1px rgba(0, 0, 0, 0.3)',
      lg: '0 10px 15px -3px rgba(0, 0, 0, 0.5), 0 4px 6px -2px rgba(0, 0, 0, 0.4)',
      xl: '0 20px 25px -5px rgba(0, 0, 0, 0.6), 0 10px 10px -5px rgba(0, 0, 0, 0.5)',
      '2xl': '0 25px 50px -12px rgba(0, 0, 0, 0.8)',
      glow: '0 0 20px rgba(129, 140, 248, 0.4)',
      glowPink: '0 0 20px rgba(244, 114, 182, 0.4)',
      glowGreen: '0 0 20px rgba(52, 211, 153, 0.4)',
    },
  },

  // Typography
  typography: {
    fontFamily: {
      sans: 'var(--font-geist-sans)',
      mono: 'var(--font-geist-mono)',
    },
    fontSize: {
      xs: '0.75rem',    // 12px
      sm: '0.875rem',   // 14px
      base: '1rem',     // 16px
      lg: '1.125rem',   // 18px
      xl: '1.25rem',    // 20px
      '2xl': '1.5rem',  // 24px
      '3xl': '1.875rem',// 30px
      '4xl': '2.25rem', // 36px
      '5xl': '3rem',    // 48px
      '6xl': '3.75rem', // 60px
    },
    fontWeight: {
      normal: 400,
      medium: 500,
      semibold: 600,
      bold: 700,
      extrabold: 800,
    },
    lineHeight: {
      tight: 1.25,
      normal: 1.5,
      relaxed: 1.75,
    },
  },

  // Animation durations
  animation: {
    duration: {
      fast: '150ms',
      normal: '300ms',
      slow: '500ms',
      slower: '700ms',
    },
    easing: {
      default: 'cubic-bezier(0.4, 0, 0.2, 1)',
      in: 'cubic-bezier(0.4, 0, 1, 1)',
      out: 'cubic-bezier(0, 0, 0.2, 1)',
      inOut: 'cubic-bezier(0.4, 0, 0.2, 1)',
      spring: 'cubic-bezier(0.34, 1.56, 0.64, 1)',
    },
  },

  // Z-index scale
  zIndex: {
    base: 0,
    dropdown: 1000,
    sticky: 1100,
    fixed: 1200,
    modal: 1300,
    popover: 1400,
    tooltip: 1500,
  },

  // Breakpoints (for reference)
  breakpoints: {
    sm: '640px',
    md: '768px',
    lg: '1024px',
    xl: '1280px',
    '2xl': '1536px',
  },
} as const;

// Helper function to get current theme colors
export function getThemeColors(mode: ThemeMode) {
  return theme.colors[mode];
}

// Helper function to get current shadows
export function getThemeShadows(mode: ThemeMode) {
  return theme.shadows[mode];
}

// Framer Motion animation variants
export const animations = {
  // Fade in/out
  fadeIn: {
    initial: { opacity: 0 },
    animate: { opacity: 1 },
    exit: { opacity: 0 },
  },

  // Slide up
  slideUp: {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0 },
    exit: { opacity: 0, y: -20 },
  },

  // Slide down
  slideDown: {
    initial: { opacity: 0, y: -20 },
    animate: { opacity: 1, y: 0 },
    exit: { opacity: 0, y: 20 },
  },

  // Scale
  scale: {
    initial: { opacity: 0, scale: 0.9 },
    animate: { opacity: 1, scale: 1 },
    exit: { opacity: 0, scale: 0.9 },
  },

  // Pop
  pop: {
    initial: { scale: 0.8, opacity: 0 },
    animate: {
      scale: 1,
      opacity: 1,
      transition: {
        type: 'spring',
        stiffness: 300,
        damping: 20,
      },
    },
    exit: { scale: 0.8, opacity: 0 },
  },

  // Stagger children
  staggerContainer: {
    animate: {
      transition: {
        staggerChildren: 0.1,
      },
    },
  },

  staggerItem: {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0 },
  },

  // Button hover
  buttonHover: {
    scale: 1.02,
    transition: { duration: 0.2 },
  },

  // Button tap
  buttonTap: {
    scale: 0.98,
  },

  // Card hover
  cardHover: {
    y: -4,
    boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
    transition: { duration: 0.2 },
  },
};
