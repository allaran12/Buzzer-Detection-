import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "CoordinX — AI Buzzer & Coordinated Behavior Detection",
  description: "AI-Powered Coordinated Inauthentic Behavior & Buzzer Network Detection System for Social Cyber Intelligence",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="id" className="h-full dark">
      <body className="min-h-full flex flex-col bg-slate-950 text-slate-100 antialiased selection:bg-indigo-500 selection:text-white font-sans">
        {children}
      </body>
    </html>
  );
}
