import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#0b0f17",
        panel: "#131a26",
        line: "#223048",
        accent: "#f5b942",
      },
    },
  },
  plugins: [],
};

export default config;