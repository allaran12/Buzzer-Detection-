import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "NEXANTARA — AI Coordinated Behavior & Buzzer Detection",
  description:
    "Sistem intelijen terbuka untuk mendeteksi perilaku terkoordinasi dan aktivitas buzzer di media sosial X (Twitter).",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="id" className="h-full scroll-smooth" suppressHydrationWarning>
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `
              try {
                const savedTheme = localStorage.getItem('theme');
                if (savedTheme === 'dark' || (!savedTheme && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
                  document.documentElement.classList.add('dark');
                } else {
                  document.documentElement.classList.remove('dark');
                }
              } catch (_) {}
            `,
          }}
        />
      </head>
      <body className="min-h-full flex flex-col bg-[var(--background)] text-[var(--foreground)] antialiased transition-colors duration-200">
        {children}
      </body>
    </html>
  );
}
