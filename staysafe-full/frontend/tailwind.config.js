/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        cream: {
          50: '#FBF7F0',
          100: '#F7F0E4',
          200: '#EFE3D0',
          300: '#E4D2B8',
        },
        terracotta: {
          300: '#E0A68A',
          400: '#D4896A',
          500: '#C57A5E',
          600: '#A85F47',
          700: '#8B4A36',
        },
        sage: {
          100: '#E8EDE3',
          200: '#CFD9C4',
          300: '#A7B897',
          400: '#7E9168',
          500: '#647A4F',
          600: '#4D6039',
          700: '#3A4A2C',
        },
        dustyblue: {
          100: '#E0E7EA',
          200: '#C2D0D6',
          300: '#97AEB7',
          400: '#6E8A95',
          500: '#54707B',
          600: '#3E5862',
        },
        rust: {
          400: '#C26A5A',
          500: '#A84A3A',
          600: '#8B3A2E',
        },
        ink: {
          700: '#4A4038',
          800: '#3A322B',
          900: '#2A2420',
        },
      },
      fontFamily: {
        heading: ['Comfortaa', 'Quicksand', 'Noto Sans Devanagari', 'Noto Sans Kannada', 'system-ui', 'sans-serif'],
        body: ['Nunito', 'Noto Sans Devanagari', 'Noto Sans Kannada', 'system-ui', 'sans-serif'],
      },
      borderRadius: {
        'xl2': '20px',
        'xl3': '28px',
      },
      boxShadow: {
        'warm-sm': '0 2px 8px rgba(122, 86, 60, 0.10)',
        'warm': '0 6px 20px rgba(122, 86, 60, 0.12)',
        'warm-lg': '0 12px 36px rgba(122, 86, 60, 0.15)',
        'warm-inset': 'inset 0 2px 4px rgba(122, 86, 60, 0.08)',
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
