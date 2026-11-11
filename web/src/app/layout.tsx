import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "CoordinX — AI Buzzer & Coordinated Behavior Detection",
  description: "Open-methodology buzzer & coordinated behavior analysis for X (Twitter). Semantic similarity, posting burst synchrony, and interaction graphs laid out transparently.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="id" className="h-full scroll-smooth">
      <body className="min-h-full flex flex-col bg-[var(--background)] text-[var(--foreground)] antialiased">
        {children}
      </body>
    </html>
  );
}
