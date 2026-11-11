import React from "react";
import { TriangleAlert } from "lucide-react";

const FOOTER_LINKS = [
  { label: "Analisis", href: "#analisis" },
  { label: "Tentang Kami", href: "#tentang-kami" },
  { label: "Cara Menggunakan", href: "#cara-menggunakan" },
  { label: "FAQ", href: "#faq" },
  {
    label: "GitHub",
    href: "https://github.com/allaran12/Buzzer-Detection-",
  },
];

export default function Footer() {
  return (
    <footer className="border-t border-[var(--border)] bg-white py-8 text-center text-xs text-[var(--muted-foreground)]">
      <div className="mx-auto max-w-screen-lg px-4 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-2 font-bold text-sm text-[var(--foreground)]">
          <div className="flex h-6 w-6 items-center justify-center rounded-md bg-[var(--primary)]/10 text-[var(--primary)]">
            <TriangleAlert size={14} />
          </div>
          <span>Buzzer Detector</span>
        </div>

        <ul className="flex flex-wrap items-center justify-center gap-5 list-none m-0 p-0">
          {FOOTER_LINKS.map((link) => (
            <li key={link.label}>
              <a
                href={link.href}
                target={link.href.startsWith("http") ? "_blank" : undefined}
                rel={
                  link.href.startsWith("http")
                    ? "noopener noreferrer"
                    : undefined
                }
                className="hover:text-[var(--foreground)] transition-colors"
              >
                {link.label}
              </a>
            </li>
          ))}
        </ul>

        <p className="m-0">
          © 2026 Buzzer Detector. Dibuat untuk analisis media sosial.
        </p>
      </div>
    </footer>
  );
}
