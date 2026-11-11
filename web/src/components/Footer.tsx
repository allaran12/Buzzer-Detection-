import Image from "next/image";
import logo from "@/app/fix logo web.png";

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
    <footer className="border-t border-[var(--border)] bg-white dark:bg-[var(--card)] py-10 text-center text-xs text-[var(--muted-foreground)] transition-colors duration-200">
      <div className="mx-auto max-w-screen-lg px-4 flex flex-col sm:flex-row items-center justify-between gap-5">
        <div className="flex items-center gap-2.5 font-extrabold text-base text-[var(--foreground)] tracking-tight">
          <Image src={logo} alt="NEXANTARA" width={36} height={36} className="h-8 w-8 object-contain" />
          <span>NEXANTARA</span>
        </div>

        {/* Links */}
        <ul className="flex flex-wrap items-center justify-center gap-6 list-none m-0 p-0">
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
                className="hover:text-[var(--primary)] dark:hover:text-white transition-colors"
              >
                {link.label}
              </a>
            </li>
          ))}
        </ul>

        {/* Copyright */}
        <p className="m-0">
          © 2026 NEXANTARA. Platform Deteksi Perilaku Terkoordinasi.
        </p>
      </div>
    </footer>
  );
}
