/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        corporate: {
          blue: '#2563EB',
          light: '#F3F4F6',
          dark: '#1E40AF'
        }
      }
    },
  },
  plugins: [],
}
