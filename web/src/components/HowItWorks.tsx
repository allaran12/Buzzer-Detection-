"use client";

import { motion } from "motion/react";
import { Link2, Cpu, BarChart3, ShieldCheck } from "lucide-react";

const STEPS = [
  {
    num: "1. Salin & Tempel URL",
    title: "Input Tautan Postingan X",
    description:
      "Salin tautan postingan X (Twitter) dari cuitan yang ingin Anda periksa, lalu tempelkan ke kolom pencarian NEXANTARA.",
    Icon: Link2,
  },
  {
    num: "2. Ekstraksi 500 Sampel",
    title: "Pengambilan Data Otomatis",
    description:
      "Sistem secara otomatis mengumpulkan hingga 500 cuitan di sekitar tautan tersebut, mencakup reply, mention, dan interaksi temporal.",
    Icon: Cpu,
  },
  {
    num: "3. Inferensi 3-Pilar AI",
    title: "Evaluasi Multidimensi",
    description:
      "Model menganalisis repetisi kalimat semantik (IndoBERTweet), sinkronisasi waktu posting serentak (LSTM), dan graf jaringan (GraphSAGE).",
    Icon: BarChart3,
  },
  {
    num: "4. Tinjau Bukti & Kluster",
    title: "Hasil & Bukti Transparan",
    description:
      "Periksa hasil analisis lengkap: skor risiko terkoordinasi, visualisasi graf kluster akun, kalimat copypasta, dan anomali polarisasi sentimen.",
    Icon: ShieldCheck,
  },
];

export default function HowItWorks() {
  return (
    <section
      id="cara-menggunakan"
      className="border-t border-[var(--border)] bg-[var(--background)] py-16 md:py-24 transition-colors duration-200"
    >
      <div className="mx-auto max-w-screen-lg px-4 md:px-6">
        <motion.div
          initial={{ opacity: 0, y: 25 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-40px" }}
          transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
          className="text-center max-w-2xl mx-auto mb-14"
        >
          <span className="eyebrow inline-block">PANDUAN PENGGUNA</span>
          <h2 className="text-3xl md:text-4xl font-extrabold tracking-tight text-[var(--foreground)] mt-1.5">
            Cara Menggunakan NEXANTARA
          </h2>
          <p className="mt-3 text-sm md:text-base text-[var(--muted-foreground)] leading-relaxed">
            Empat langkah mudah dari URL postingan hingga pembuktian pola buzzer
          </p>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {STEPS.map((step, idx) => {
            const Icon = step.Icon;
            return (
              <motion.div
                key={step.num}
                initial={{ opacity: 0, y: 25 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: "-20px" }}
                transition={{
                  duration: 0.45,
                  delay: idx * 0.08,
                  ease: [0.16, 1, 0.3, 1],
                }}
                whileHover={{ y: -4 }}
                className="rounded-2xl border border-[var(--border)] bg-white dark:bg-[var(--card)] p-6 md:p-7 shadow-xs hover:border-[var(--primary)]/50 hover:shadow-md transition-all duration-200"
              >
                <div className="flex items-center gap-4 mb-3.5">
                  <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-blue-50 dark:bg-blue-950/40 text-[var(--primary)] border border-blue-100 dark:border-blue-900/40">
                    <Icon size={22} />
                  </div>
                  <div>
                    <h3 className="text-lg font-bold text-[var(--foreground)]">
                      {step.num}
                    </h3>
                    <p className="text-xs font-medium text-[var(--muted-foreground)]">
                      {step.title}
                    </p>
                  </div>
                </div>
                <p className="text-sm text-[var(--foreground)]/80 leading-relaxed mt-2">
                  {step.description}
                </p>
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
