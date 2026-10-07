/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        // Charte SenTerangaSafe (logo)
        brand: {
          blue: "#1B4F9C",
          "blue-light": "#2B6BC4",
          "blue-soft": "#E8F0FA",
          gold: "#C4A035",
          "gold-light": "#D4B84A",
          "gold-soft": "#FBF6E8",
          green: "#1B7A4A",
          "green-light": "#22A05A",
          "green-soft": "#E8F6EE",
        },
        primary: {
          50: "#E8F0FA",
          100: "#D0E1F5",
          200: "#A1C3EB",
          300: "#72A5E1",
          400: "#4387D7",
          500: "#2B6BC4",
          600: "#1B4F9C",
          700: "#163F7D",
          800: "#112F5E",
          900: "#0C1F3E",
        },
        surface: {
          DEFAULT: "#F7F5F0",
          card: "#FFFFFF",
          muted: "#F0EDE6",
        },
        success: "#1B7A4A",
        warning: "#C4A035",
        danger: "#DC2626",
      },
      fontFamily: {
        sans: [
          "Inter",
          "ui-sans-serif",
          "system-ui",
          "-apple-system",
          "Segoe UI",
          "Roboto",
          "sans-serif",
        ],
      },
      boxShadow: {
        soft: "0 1px 3px rgba(27, 79, 156, 0.06), 0 4px 16px rgba(27, 79, 156, 0.06)",
        card: "0 1px 2px rgba(15, 23, 42, 0.04), 0 8px 24px rgba(15, 23, 42, 0.06)",
        nav: "0 1px 0 rgba(15, 23, 42, 0.06), 0 4px 20px rgba(15, 23, 42, 0.04)",
      },
      borderRadius: {
        xl: "0.875rem",
        "2xl": "1rem",
      },
    },
  },
  plugins: [],
};
