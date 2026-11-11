"use client";

import { useState } from "react";
import { Menu, X, TriangleAlert } from "lucide-react";

const NAV_LINKS = [
  { label: "Analisis", href: "#analisis" },
  { label: "Tentang Kami", href: "#tentang-kami" },
  { label: "Cara Menggunakan", href: "#cara-menggunakan" },
  { label: "FAQ", href: "#faq" },
];

export default function Navbar() {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <header className="sticky top-0 z-40 w-full border-b border-[var(--border)] bg-white/95 backdrop-blur-sm">
      <div className="mx-auto flex h-16 max-w-screen-lg items-center justify-between px-4 md:px-6">
        {/* Logo / Brand */}
        <a href="#" className="flex items-center space-x-2 select-none">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-[var(--primary)]/10 text-[var(--primary)]">
            <TriangleAlert size={20} />
          </div>
          <span className="font-bold text-lg md:text-xl text-[var(--foreground)] tracking-tight">
            Buzzer Detector
          </span>
        </a>

        {/* Desktop Nav */}
        <nav className="hidden md:flex items-center gap-6">
          {NAV_LINKS.map((link) => (
            <a
              key={link.href}
              href={link.href}
              className="text-sm font-medium text-[var(--muted-foreground)] hover:text-[var(--foreground)] transition-colors"
            >
              {link.label}
            </a>
          ))}
        </nav>

        {/* Right side */}
        <div className="hidden md:flex items-center gap-3">
          <div className="flex items-center gap-1.5 rounded-full border border-[var(--border)] bg-[var(--card)] px-3 py-1 text-xs font-medium text-[var(--muted-foreground)]">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[var(--accent-go)] opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-[var(--accent-go)]" />
            </span>
            Sistem Siap
          </div>

          <a
            href="#analisis"
            className="rounded-lg bg-[var(--primary)] px-4 py-2 text-xs font-semibold text-white hover:opacity-90 transition-opacity"
          >
            Mulai Analisis
          </a>
        </div>

        {/* Mobile menu toggle */}
        <button
          type="button"
          className="md:hidden p-2 rounded-md text-[var(--foreground)] hover:bg-[var(--card)]"
          onClick={() => setMobileOpen((o) => !o)}
          aria-label="Toggle Menu"
        >
          {mobileOpen ? <X size={22} /> : <Menu size={22} />}
        </button>
      </div>

      {/* Mobile dropdown */}
      {mobileOpen && (
        <div className="md:hidden border-t border-[var(--border)] bg-white px-4 pb-4 pt-2 shadow-lg">
          <nav className="flex flex-col gap-1">
            {NAV_LINKS.map((link) => (
              <a
                key={link.href}
                href={link.href}
                onClick={() => setMobileOpen(false)}
                className="rounded-md px-3 py-2 text-sm font-medium text-[var(--muted-foreground)] hover:bg-[var(--card)] hover:text-[var(--foreground)] transition-colors"
              >
                {link.label}
              </a>
            ))}
          </nav>
          <div className="mt-3 pt-3 border-t border-[var(--border)] flex flex-col gap-2">
            <a
              href="#analisis"
              onClick={() => setMobileOpen(false)}
              className="rounded-lg bg-[var(--primary)] px-4 py-2.5 text-center text-xs font-semibold text-white hover:opacity-90 transition-opacity"
            >
              Mulai Analisis
            </a>
          </div>
        </div>
      )}
    </header>
  );
}
