import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        slate950: "#020617"
      },
      boxShadow: {
        glow: "0 0 0 1px rgba(148, 163, 184, 0.2), 0 20px 60px rgba(2, 6, 23, 0.6)"
      }
    }
  },
  plugins: []
};

export default config;
