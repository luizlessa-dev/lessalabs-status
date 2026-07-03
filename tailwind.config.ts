import type { Config } from "tailwindcss";

export default {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50:  "#eff6ff",
          500: "#1A5CFF",
          600: "#1449CC",
          900: "#0B1222",
        },
        teal: {
          500: "#009E88",
          400: "#2DD4BF",
        },
        amber: {
          500: "#E07B00",
        },
      },
      fontFamily: {
        sans: ["var(--font-sans)", "system-ui", "sans-serif"],
        mono: ["var(--font-mono)", "monospace"],
      },
    },
  },
  plugins: [],
} satisfies Config;
