/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        brand: { 50: '#f0f4ff', 100: '#dbe4ff', 200: '#bac8ff', 500: '#1746a2', 600: '#0d2f7a', 700: '#0c1425' },
      },
      fontFamily: { sans: ['Instrument Sans', 'DM Sans', 'system-ui', 'sans-serif'] }
    }
  },
  plugins: []
}
