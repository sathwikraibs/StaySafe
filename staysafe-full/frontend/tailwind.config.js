/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      // TrustLight colours, taken from the lighthouse logo.
      // brand = the night-sky indigo of the icon, beam = its warm light.
      // sage = SAFE (green), terracotta = CAREFUL (amber), rust = RISKY (red).
      // cream = white surfaces and soft greys, dustyblue = quiet slate text, ink = deep navy text.
      colors: {
        mist: '#F5F6FB',
        brand: {
          50: '#EFF0FF',
          100: '#E2E4FD',
          200: '#C8CBF8',
          300: '#A2A6EE',
          400: '#7275DB',
          500: '#4D4BC4',
          600: '#3730A3',
          700: '#2D2786',
          800: '#221E66',
          900: '#181548',
        },
        beam: {
          100: '#FFF6DA',
          200: '#FDE68A',
          300: '#FCD34D',
          400: '#FBBF24',
          500: '#F0A500',
          600: '#B07A0A',
        },
        cream: {
          50: '#FFFFFF',
          100: '#F4F5FA',
          200: '#E6E8F1',
          300: '#D2D6E4',
        },
        terracotta: {
          300: '#F6CF95',
          400: '#EDA23B',
          500: '#D98324',
          600: '#B4651A',
          700: '#8C4C12',
        },
        sage: {
          100: '#E3F4EB',
          200: '#C5E8D4',
          300: '#92CFAD',
          400: '#4FB07F',
          500: '#22905C',
          600: '#1A784B',
          700: '#135E3B',
        },
        dustyblue: {
          100: '#ECEEF6',
          200: '#D7DBE8',
          300: '#ABB2C9',
          400: '#7E87A3',
          500: '#5F6886',
          600: '#4A526E',
        },
        rust: {
          300: '#F0A79E',
          400: '#E5675A',
          500: '#CC3A2E',
          600: '#A52A21',
        },
        ink: {
          700: '#363A57',
          800: '#23273F',
          900: '#14172E',
        },
      },
      fontFamily: {
        heading: ['"Baloo 2"', '"Baloo Tamma 2"', 'system-ui', 'sans-serif'],
        body: ['"Noto Sans"', '"Noto Sans Devanagari"', '"Noto Sans Kannada"', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'SFMono-Regular', 'Menlo', 'monospace'],
      },
      borderRadius: {
        'xl2': '20px',
        'xl3': '28px',
      },
      boxShadow: {
        'warm-sm': '0 1px 2px rgba(20, 23, 60, 0.05), 0 2px 8px rgba(20, 23, 60, 0.05)',
        'warm': '0 1px 3px rgba(20, 23, 60, 0.05), 0 8px 24px rgba(20, 23, 60, 0.07)',
        'warm-lg': '0 4px 10px rgba(20, 23, 60, 0.06), 0 18px 44px rgba(20, 23, 60, 0.12)',
        'warm-inset': 'inset 0 2px 4px rgba(20, 23, 60, 0.06)',
      },
      transitionTimingFunction: {
        'bounce-soft': 'cubic-bezier(0.34, 1.56, 0.64, 1)',
      },
      keyframes: {
        'breath': {
          '0%, 100%': { transform: 'scale(0.85)', opacity: '0.6' },
          '50%': { transform: 'scale(1.1)', opacity: '1' },
        },
        'breath-delayed': {
          '0%, 100%': { transform: 'scale(0.7)', opacity: '0.4' },
          '50%': { transform: 'scale(1.0)', opacity: '0.8' },
        },
        'fade-up': {
          '0%': { opacity: '0', transform: 'translateY(12px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        'lift': {
          '0%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-4px)' },
          '100%': { transform: 'translateY(0)' },
        },
      },
      animation: {
        'breath': 'breath 1.8s ease-in-out infinite',
        'breath-delayed': 'breath-delayed 1.8s ease-in-out 0.3s infinite',
        'fade-up': 'fade-up 0.5s cubic-bezier(0.34, 1.56, 0.64, 1) both',
        'lift': 'lift 0.4s ease-in-out',
      },
    },
  },
  plugins: [],
};
