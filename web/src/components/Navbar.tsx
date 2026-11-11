"use client";

import { useState, useEffect } from "react";
import Image from "next/image";
import { Menu, X, Sun, Moon } from "lucide-react";
import logo from "@/app/fix logo web.png";

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
        <a href="#" className="select-none group">
          <Image
            src={logo}
            alt="NEXANTARA"
            width={48}
            height={48}
            className="h-11 w-11 object-contain transition-transform group-hover:scale-105"
            priority
          />
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

        </div>
      )}
    </header>
  );
}
