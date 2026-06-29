/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class', // Enable dark mode with class strategy
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        purple: {
          primary: '#7B5CF0',
          light: '#A78BFA',
          dim: 'rgba(123, 92, 240, 0.12)',
          dim2: 'rgba(123, 92, 240, 0.16)',
        },
        black: {
          cta: '#0F0F11',
          text: '#1A1A22',
        },
        gray: {
          bg: '#EBEBEE',
          card: '#F5F5F7',
          input: '#EFEFF2',
          muted: '#8585A0',
          placeholder: '#ADADC0',
          border: 'rgba(0, 0, 0, 0.07)',
          text: '#1A1A22',
        },
        green: {
          DEFAULT: '#16A34A',
          dim: 'rgba(22, 163, 74, 0.10)',
        },
        amber: {
          DEFAULT: '#D97706',
          dim: 'rgba(217, 119, 6, 0.10)',
        },
        red: {
          DEFAULT: '#DC2626',
          dim: 'rgba(220, 38, 38, 0.08)',
        },
      },
      fontFamily: {
        syne: ['Syne', 'sans-serif'],
        sans: ['DM Sans', 'system-ui', 'sans-serif'],
      },
      spacing: {
        xs: '6px',
        sm: '10px',
        md: '14px',
        lg: '22px',
        xl: '32px',
        '2xl': '44px',
        panel: '64px',
      },
      borderRadius: {
        sm: '8px',
        md: '11px',
        lg: '16px',
        card: '28px',
      },
      boxShadow: {
        sm: '0 2px 8px rgba(0, 0, 0, 0.06)',
        md: '0 2px 16px rgba(0, 0, 0, 0.08)',
        card: '0 8px 40px rgba(0, 0, 0, 0.10)',
        btn: '0 6px 24px rgba(0, 0, 0, 0.22)',
        'focus-ring': '0 0 0 3px rgba(123, 92, 240, 0.12)',
      },
      keyframes: {
        fadeUp: {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        pulse: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.5' },
        },
      },
      animation: {
        'fade-up': 'fadeUp 0.6s cubic-bezier(0.22, 1, 0.36, 1)',
        'pulse-ring': 'pulse 2.5s ease-in-out infinite',
      },
    },
  },
  plugins: [
    function ({ addUtilities }) {
      addUtilities({
        '.scrollbar-hide': {
          /* Firefox */
          'scrollbar-width': 'none',
          /* Safari and Chrome */
          '&::-webkit-scrollbar': {
            display: 'none',
          },
        },
      });
    },
  ],
}
