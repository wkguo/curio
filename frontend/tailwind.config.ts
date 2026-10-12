import type { Config } from "tailwindcss";
import animate from "tailwindcss-animate";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    container: { center: true, padding: "1rem" },
    extend: {
      fontFamily: {
        sans: ["var(--font-nunito)", "ui-rounded", "system-ui", "sans-serif"],
        mono: ["var(--font-mono)", "ui-monospace", "monospace"],
      },
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: { DEFAULT: "hsl(var(--primary))", foreground: "hsl(var(--primary-foreground))" },
        muted: { DEFAULT: "hsl(var(--muted))", foreground: "hsl(var(--muted-foreground))" },
        card: { DEFAULT: "hsl(var(--card))", foreground: "hsl(var(--card-foreground))" },
        cream: "#FFF9F1",
        curio: { 50: "#F4F1FF", 100: "#EAE4FF", 200: "#D6CBFF", 300: "#B8A6FF", 400: "#9A80FF", 500: "#7C5CFF", 600: "#6842F5", 700: "#5631D6", 800: "#4527AD", 900: "#2E1F75" },
        mint: { 50: "#EAFBF3", 100: "#CFF5E3", 200: "#A6EDCB", 300: "#6FE0AE", 400: "#3DD08E", 500: "#1FB978", 600: "#159A63", 700: "#0F7A4F" },
        sun: { 50: "#FFF8E6", 100: "#FFEFC2", 200: "#FFE394", 300: "#FFD66B", 400: "#FFC53D", 500: "#F5A70A", 600: "#C98500", 700: "#9A6500" },
        coral: { 50: "#FFF1EC", 100: "#FFE0D5", 200: "#FFC4B0", 300: "#FFA487", 400: "#FF8660", 500: "#FF6B3D", 600: "#E4501F", 700: "#B63A12" },
        sky: { 50: "#EAF6FF", 100: "#D2ECFF", 200: "#A9DAFF", 300: "#8CCBFF", 400: "#57B2FF", 500: "#2E97F5", 600: "#1B7AD6", 700: "#135DA6" },
        ink: { DEFAULT: "#1E1B3A", 900: "#1E1B3A", 800: "#2B2850", 700: "#3A3658", 600: "#55516F", 500: "#6B6887", 400: "#9A97B0", 300: "#C9C7D8", 200: "#E6E4EF", 100: "#F3F2F8", 50: "#F9F8FC" },
      },
      borderRadius: { "4xl": "2rem", lg: "var(--radius)", md: "calc(var(--radius) - 4px)", sm: "calc(var(--radius) - 8px)" },
      boxShadow: {
        soft: "0 1px 2px rgba(30,27,58,0.04), 0 8px 24px -12px rgba(30,27,58,0.12)",
        float: "0 2px 4px rgba(30,27,58,0.04), 0 24px 48px -20px rgba(64,40,170,0.28)",
        glow: "0 0 0 6px rgba(124,92,255,0.12)",
      },
      keyframes: {
        "float-y": { "0%,100%": { transform: "translateY(0)" }, "50%": { transform: "translateY(-6px)" } },
        wiggle: { "0%,100%": { transform: "rotate(-3deg)" }, "50%": { transform: "rotate(3deg)" } },
        shimmer: { "0%": { backgroundPosition: "-200% 0" }, "100%": { backgroundPosition: "200% 0" } },
        "pop-in": { "0%": { transform: "scale(.6)", opacity: "0" }, "70%": { transform: "scale(1.08)" }, "100%": { transform: "scale(1)", opacity: "1" } },
        "dash-flow": { to: { strokeDashoffset: "-20" } },
      },
      animation: {
        "float-y": "float-y 4s ease-in-out infinite",
        wiggle: "wiggle 1.2s ease-in-out infinite",
        shimmer: "shimmer 2.2s linear infinite",
        "pop-in": "pop-in .45s cubic-bezier(.2,.9,.3,1.3) both",
        "dash-flow": "dash-flow 1s linear infinite",
      },
    },
  },
  plugins: [animate],
};

export default config;
