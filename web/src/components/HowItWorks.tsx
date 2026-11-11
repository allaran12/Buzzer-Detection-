"use client";

import { motion } from "motion/react";
import { Download, FileText, BarChart3, AlertTriangle } from "lucide-react";

const STEPS = [
  {
    num: "1. Ambil Data",
    title: "Scrape cuitan / tagar dari X",
    description:
      'Masukkan URL cuitan atau #tagar di tab "Scrape X/Twitter" dan klik "Analisis Pola". Aplikasi akan mengambil cuitan terkait secara otomatis.',
    Icon: Download,
  },
  {
    num: "2. Input Manual",
    title: "Atau masukkan teks secara manual",
    description:
      'Jika Anda memiliki teks komentar/cuitan dari sumber lain, Anda dapat menempelkannya di tab "Input Manual". Pastikan setiap baris berisi satu cuitan.',
    Icon: FileText,
  },
  {
    num: "3. Analisis Pola",
    title: "Jalankan analisis pola aktivitas",
    description:
      'Klik "Analisis Pola" untuk memulai proses. Sistem akan menganalisis pola linguistik IndoBERTweet, frasa umum, repetisi, dan anomali waktu burst.',
    Icon: BarChart3,
  },
  {
    num: "4. Interpretasi Hasil",
    title: "Pahami hasil analisis",
    description:
      "Lihat hasil analisis di tab yang berbeda: Visualisasi Pola, Analisis Frasa, Analisis Sentimen, dan Kluster Pengguna. Skor tinggi menunjukkan kemungkinan aktivitas buzzer.",
    Icon: AlertTriangle,
  },
];

export default function HowItWorks() {
  return (
    <section id="cara-menggunakan" className="border-t border-[var(--border)] bg-[var(--background)] py-16 md:py-20">
      <div className="mx-auto max-w-screen-lg px-4 md:px-6">
        <div className="text-center max-w-2xl mx-auto mb-12">
          <h2 className="text-3xl md:text-4xl font-bold tracking-tight text-[var(--foreground)]">
            Cara Menggunakan
          </h2>
          <p className="mt-3 text-sm md:text-base text-[var(--muted-foreground)] leading-relaxed">
            Panduan langkah demi langkah untuk menggunakan Buzzer Detector
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {STEPS.map((step, idx) => {
            const Icon = step.Icon;
            return (
              <motion.div
                key={step.num}
                initial={{ opacity: 0, y: 16 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.35, delay: idx * 0.08 }}
                className="rounded-xl border border-[var(--border)] bg-white p-6 shadow-xs hover:border-[var(--primary)]/40 hover:shadow-sm transition-all"
              >
                <div className="flex items-center gap-4 mb-3">
                  <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-blue-50 text-[var(--primary)]">
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
