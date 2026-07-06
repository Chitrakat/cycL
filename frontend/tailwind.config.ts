import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        "cy-bg": "#08090b",
        "cy-surface": "#1a1b1f",
        "cy-card": "#2f3136",
        "cy-text": "#f2f2f2",
        "cy-muted": "#8e9096",
        "cy-green": "#62b30f",
        "cy-orange": "#ff9727",
        "cy-red": "#ff3b43",
        "cy-yellow": "#ffd21f",
      },
      fontFamily: {
        plex: ['"IBM Plex Mono"', "monospace"],
      },
      boxShadow: {
        neonGreen: "0 0 0 2px rgba(98,179,15,0.35), 0 0 24px rgba(98,179,15,0.45)",
        neonOrange: "0 0 0 2px rgba(255,151,39,0.35), 0 0 24px rgba(255,151,39,0.45)",
        neonRed: "0 0 0 2px rgba(255,59,67,0.35), 0 0 24px rgba(255,59,67,0.45)",
      },
      keyframes: {
        pulseSlow: {
          "0%, 100%": { transform: "scale(1)", opacity: "1" },
          "50%": { transform: "scale(1.03)", opacity: "0.9" },
        },
      },
      animation: {
        pulseSlow: "pulseSlow 1.4s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};

export default config;
