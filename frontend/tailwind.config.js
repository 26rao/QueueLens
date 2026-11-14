/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        sidebar: '#0F172A',
        accent: '#0D9488',
        background: '#F8FAFC',
        emergency: '#DC2626',
        urgent: '#D97706',
        normal: '#0D9488',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
