/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ['class'],
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#d7fff3',
          foreground: '#00382f',
        },
        'primary-container': '#00f5d4',
        'on-primary-container': '#006c5c',
        'primary-fixed': '#26fedc',
        'on-primary-fixed': '#00201a',
        'primary-fixed-dim': '#00dfc1',
        secondary: {
          DEFAULT: '#82d3ff',
          foreground: '#003549',
        },
        'secondary-container': '#00bbf9',
        'on-secondary-container': '#004761',
        'secondary-fixed': '#c3e8ff',
        'on-secondary-fixed': '#001e2c',
        'secondary-fixed-dim': '#79d1ff',
        accent: {
          DEFAULT: '#8B5CF6',
          foreground: '#FFFFFF',
        },
        success: {
          DEFAULT: '#10B981',
          foreground: '#FFFFFF',
        },
        warning: {
          DEFAULT: '#F59E0B',
          foreground: '#FFFFFF',
        },
        error: {
          DEFAULT: '#ffb4ab',
          foreground: '#690005',
        },
        'error-container': '#93000a',
        'on-error-container': '#ffdad6',
        info: {
          DEFAULT: '#3B82F6',
          foreground: '#FFFFFF',
        },
        background: '#131318',
        'on-background': '#e4e1e9',
        surface: '#131318',
        'surface-dim': '#131318',
        'surface-bright': '#39383e',
        'surface-container-lowest': '#0e0e13',
        'surface-container-low': '#1b1b20',
        'surface-container': '#1f1f25',
        'surface-container-high': '#2a292f',
        'surface-container-highest': '#35343a',
        'on-surface': '#e4e1e9',
        'on-surface-variant': '#b9cac4',
        'surface-variant': '#35343a',
        outline: '#83948f',
        'outline-variant': '#3a4a46',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        headline: ['Space Grotesk', 'sans-serif'],
        body: ['Inter', 'sans-serif'],
        label: ['Inter', 'sans-serif'],
      },
    },
  },
  plugins: [],
};
