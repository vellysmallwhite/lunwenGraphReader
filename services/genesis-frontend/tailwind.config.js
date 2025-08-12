/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        'deep-space': '#0C0C1E',
        'cyber-blue': '#00F6FF',
        'neon-pink': '#FF00E5',
        'electric-green': '#39FF14',
        'starlight': '#E0E0FF',
      },
      fontFamily: {
        'orbitron': ['Orbitron', 'monospace'],
        'roboto-mono': ['Roboto Mono', 'monospace'],
      },
      animation: {
        'pulse-glow': 'pulse-glow 2s ease-in-out infinite alternate',
        'float': 'float 6s ease-in-out infinite',
        'star-twinkle': 'star-twinkle 4s linear infinite',
        'nebula-drift': 'nebula-drift 20s ease-in-out infinite',
        'ring-rotation': 'ring-rotation 4s linear infinite',
      },
      keyframes: {
        'pulse-glow': {
          '0%': { boxShadow: '0 0 20px rgba(0, 246, 255, 0.5)' },
          '100%': { boxShadow: '0 0 40px rgba(0, 246, 255, 0.8)' }
        },
        'float': {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-10px)' }
        },
        'star-twinkle': {
          '0%, 100%': { opacity: '0.3' },
          '50%': { opacity: '1' }
        },
        'nebula-drift': {
          '0%, 100%': { transform: 'translate(0, 0) scale(1)' },
          '33%': { transform: 'translate(-20px, -10px) scale(1.1)' },
          '66%': { transform: 'translate(20px, 10px) scale(0.9)' }
        },
        'ring-rotation': {
          '0%': { transform: 'rotate(0deg)' },
          '100%': { transform: 'rotate(360deg)' }
        }
      }
    },
  },
  plugins: [],
}
