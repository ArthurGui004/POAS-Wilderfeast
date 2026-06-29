/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        wilddark: '#12100E',   // Fundo breu da floresta
        wildcard: '#1C1917',   // Painéis internos rústicos
        wildorange: '#E05A10', // Laranja fogo/logotipo oficial
        wildgreen: '#2E4A3E',  // Verde caçador secundário
      },
    },
  },
  plugins: [],
}