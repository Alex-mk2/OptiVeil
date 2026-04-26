/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        cyber: {
          black: '#0a0a0b',
          dark: '#121214',
          green: '#00ffcc',
          red: '#ff4b4b',
        }
      }
    },
  },
  plugins: [],
}