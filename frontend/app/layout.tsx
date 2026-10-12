import type { Metadata, Viewport } from "next";
import { JetBrains_Mono, Nunito } from "next/font/google";

import { Providers } from "@/components/layout/providers";

import "./globals.css";

const nunito = Nunito({ subsets: ["latin"], weight: ["400", "500", "600", "700", "800", "900"], variable: "--font-nunito" });
const mono = JetBrains_Mono({ subsets: ["latin"], weight: ["400", "600"], variable: "--font-mono" });

export const metadata: Metadata = {
  title: { default: "Curio — Don't just answer. Understand.", template: "%s · Curio" },
  description: "Curio verifies whether primary school students truly understand science — not just whether they got the answer right.",
  icons: { icon: "/favicon.svg" },
};

export const viewport: Viewport = { themeColor: "#7C5CFF" };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${nunito.variable} ${mono.variable}`}>
      <body className="min-h-screen font-sans">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
