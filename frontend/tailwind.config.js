/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './index.html',
    './src/**/*.{vue,js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        // 浅色主题
        canvas: '#F6F8FA',
        surface: '#FFFFFF',
        ink: {
          DEFAULT: '#0A0A0A',
          soft: '#3D3D3D',
          muted: '#6B7280',
          dim: '#9CA3AF',
        },
        line: {
          DEFAULT: '#E5E7EB',
          hover: '#D1D5DB',
        },
        // 沿用品牌色（在浅底上仍能良好呈现）
        jade: {
          DEFAULT: '#3A7A6E',
          dim: '#5A9388',
          soft: 'rgba(58, 122, 110, 0.10)',
        },
        cinnabar: {
          DEFAULT: '#8B3A3A',
          dim: '#A85050',
          soft: 'rgba(139, 58, 58, 0.10)',
        },
        gold: {
          DEFAULT: '#C9A961',
          soft: 'rgba(201, 169, 97, 0.14)',
        },
      },
      borderRadius: {
        // 统一卡片圆角 20px
        card: '20px',
      },
      boxShadow: {
        // 轻微阴影
        card: '0 1px 2px rgba(15, 23, 42, 0.04), 0 4px 12px rgba(15, 23, 42, 0.04)',
        'card-hover': '0 2px 4px rgba(15, 23, 42, 0.06), 0 8px 24px rgba(15, 23, 42, 0.08)',
        hero: '0 20px 60px -20px rgba(15, 23, 42, 0.18)',
      },
      fontFamily: {
        sans: ['Inter', 'Noto Sans SC', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'Consolas', 'monospace'],
      },
      keyframes: {
        'fade-up': {
          '0%': { opacity: '0', transform: 'translateY(12px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        'fade-in': {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
      },
      animation: {
        'fade-up': 'fade-up 0.6s cubic-bezier(0.16, 1, 0.3, 1) both',
        'fade-in': 'fade-in 0.6s ease-out both',
      },
    },
  },
  plugins: [],
}
