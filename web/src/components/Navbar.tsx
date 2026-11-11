"use client";

import { useState, useEffect } from "react";
import { Menu, X, ShieldAlert, Sun, Moon } from "lucide-react";

const NAV_LINKS = [
  { label: "Analisis", href: "#analisis" },
  { label: "Tentang Kami", href: "#tentang-kami" },
  { label: "Cara Menggunakan", href: "#cara-menggunakan" },
  { label: "FAQ", href: "#faq" },
];

export default function Navbar() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [isDark, setIsDark] = useState(false);

  useEffect(() => {
    // Check initial dark mode state
    const isDarkMode = document.documentElement.classList.contains("dark");
    if (isDarkMode) {
      const timer = setTimeout(() => setIsDark(true), 0);
      return () => clearTimeout(timer);
    }
  }, []);

  const toggleDarkMode = () => {
    const nextDark = !isDark;
    setIsDark(nextDark);
    if (nextDark) {
      document.documentElement.classList.add("dark");
      localStorage.setItem("theme", "dark");
    } else {
      document.documentElement.classList.remove("dark");
      localStorage.setItem("theme", "light");
    }
  };

  return (
    <header className="sticky top-0 z-40 w-full border-b border-[var(--border)] bg-white/95 dark:bg-[var(--card)]/90 backdrop-blur-md transition-colors duration-200">
      <div className="mx-auto flex h-16 max-w-screen-lg items-center justify-between px-4 md:px-6">
        {/* Logo / Brand — NEXANTARA with ShieldAlert */}
        <a href="#" className="flex items-center space-x-2.5 select-none group">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-tr from-blue-600 via-indigo-600 to-blue-500 text-white shadow-md shadow-blue-500/20 group-hover:scale-105 transition-transform">
            <ShieldAlert size={20} />
          </div>
          <div className="flex flex-col">
            <span className="font-extrabold text-xl text-[var(--foreground)] tracking-tight leading-none">
              NEXANTARA
            </span>
            <span className="text-[10px] font-semibold text-[var(--primary)] uppercase tracking-widest mt-0.5">
              Buzzer Intelligence
            </span>
          </div>
        </a>

        {/* Desktop Nav */}
        <nav className="hidden md:flex items-center gap-6">
          {NAV_LINKS.map((link) => (
            <a
              key={link.href}
              href={link.href}
              className="text-sm font-medium text-[var(--muted-foreground)] hover:text-[var(--primary)] dark:hover:text-white transition-colors"
            >
              {link.label}
            </a>
          ))}
        </nav>

        {/* Right side: Dark Mode Toggle + CTA */}
        <div className="hidden md:flex items-center gap-3">
          {/* Theme Toggle Button */}
          <button
            type="button"
            onClick={toggleDarkMode}
            aria-label="Toggle dark mode"
            className="flex h-9 w-9 items-center justify-center rounded-lg border border-[var(--border)] bg-[var(--card)] text-[var(--foreground)] hover:bg-[var(--card-subtle)] transition-colors cursor-pointer"
          >
            {isDark ? (
              <Sun size={17} className="text-amber-400 animate-in fade-in" />
            ) : (
              <Moon size={17} className="text-slate-600 animate-in fade-in" />
            )}
          </button>

          <a
            href="#analisis"
            className="rounded-lg bg-[var(--primary)] px-4 py-2 text-xs font-semibold text-white hover:opacity-90 transition-opacity shadow-xs shadow-blue-600/20"
          >
            Mulai Analisis
          </a>
        </div>

        {/* Mobile controls */}
        <div className="flex md:hidden items-center gap-2">
          <button
            type="button"
            onClick={toggleDarkMode}
            aria-label="Toggle dark mode"
            className="flex h-9 w-9 items-center justify-center rounded-lg border border-[var(--border)] bg-[var(--card)] text-[var(--foreground)]"
          >
            {isDark ? (
              <Sun size={17} className="text-amber-400" />
            ) : (
              <Moon size={17} className="text-slate-600" />
            )}
          </button>

          <button
            type="button"
            className="p-2 rounded-md text-[var(--foreground)] hover:bg-[var(--card)]"
            onClick={() => setMobileOpen((o) => !o)}
            aria-label="Toggle Menu"
          >
            {mobileOpen ? <X size={22} /> : <Menu size={22} />}
          </button>
        </div>
      </div>

      {/* Mobile dropdown */}
      {mobileOpen && (
        <div className="md:hidden border-t border-[var(--border)] bg-white dark:bg-[var(--card)] px-4 pb-4 pt-2 shadow-xl animate-in slide-in-from-top-2">
          <nav className="flex flex-col gap-1">
            {NAV_LINKS.map((link) => (
              <a
                key={link.href}
                href={link.href}
                onClick={() => setMobileOpen(false)}
                className="rounded-md px-3 py-2 text-sm font-medium text-[var(--muted-foreground)] hover:bg-[var(--card-subtle)] hover:text-[var(--foreground)] transition-colors"
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
