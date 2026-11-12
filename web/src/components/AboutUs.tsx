"use client";

import { motion } from "motion/react";
import { Search, Network, Users, Smile } from "lucide-react";

const FEATURES = [
  {
    title: "Deteksi Pola",
    tagline: "Mengidentifikasi pola narasi yang mencurigakan",
    description:
      "Algoritma NEXANTARA menganalisis struktur kalimat, frasa umum, repetisi semantik IndoBERTweet, dan anomali waktu untuk mendeteksi aktivitas buzzer yang terkoordinasi.",
    Icon: Search,
    iconBg: "bg-blue-50 dark:bg-blue-950/40 text-[var(--primary)] border border-blue-100 dark:border-blue-900/50",
  },
  {
    title: "Visualisasi Data",
    tagline: "Melihat pola dengan visualisasi interaktif",
    description:
      "Visualisasi grafik interaktif membantu Anda memahami topologi hubungan antar akun, sentralitas mention/reply, serta memetakan kluster aktivitas yang mencurigakan.",
    Icon: Network,
    iconBg: "bg-indigo-50 dark:bg-indigo-950/40 text-indigo-500 border border-indigo-100 dark:border-indigo-900/50",
  },
  {
    title: "Analisis Pengguna",
    tagline: "Mengidentifikasi kluster pengguna mencurigakan",
    description:
      "Sistem mengelompokkan pengguna berdasarkan pola posting serentak (temporal burst interval) dan rasio anomali profil untuk membongkar jaringan akun yang dikoordinasikan.",
    Icon: Users,
    iconBg: "bg-emerald-50 dark:bg-emerald-950/40 text-emerald-500 border border-emerald-100 dark:border-emerald-900/50",
  },
  {
    title: "Analisis Sentimen",
    tagline: "Mendeteksi anomali dalam polarisasi cuitan",
    description:
      "Analisis sentimen mendeteksi polarisasi ekstrem dan distribusi sentimen yang seragam secara tidak wajar terhadap figur atau isu tertentu dalam durasi singkat.",
    Icon: Smile,
    iconBg: "bg-amber-50 dark:bg-amber-950/40 text-amber-500 border border-amber-100 dark:border-amber-900/50",
  },
];

export default function AboutUs() {
  return (
    <section
      id="tentang-kami"
      className="border-t border-[var(--border)] bg-white dark:bg-[var(--card)] py-16 md:py-24 transition-colors duration-200"
    >
      <div className="mx-auto max-w-screen-lg px-4 md:px-6">
        <motion.div
          initial={false}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-40px" }}
          transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
          className="text-center max-w-2xl mx-auto mb-14"
        >
          <h2 className="text-3xl md:text-4xl font-extrabold tracking-tight text-[var(--foreground)] mt-1.5">
            Tentang NEXANTARA
          </h2>
          <p className="mt-3 text-sm md:text-base text-[var(--muted-foreground)] leading-relaxed">
            Platform intelijen media sosial canggih berbasis AI untuk mendeteksi perilaku manipulatif, kampanye bot terkoordinasi, dan operasi siber di Indonesia.
          </p>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {FEATURES.map((feat, idx) => {
            const Icon = feat.Icon;
            return (
              <motion.div
                key={feat.title}
                initial={false}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: "-20px" }}
                transition={{
                  duration: 0.45,
                  delay: idx * 0.08,
                  ease: [0.16, 1, 0.3, 1],
                }}
                whileHover={{ y: -4 }}
                className="flex flex-col justify-between rounded-2xl border border-[var(--border)] bg-[var(--background)] p-6 md:p-7 shadow-xs hover:border-[var(--primary)]/50 hover:shadow-md transition-all duration-200"
              >
                <div>
                  <div className="flex items-center gap-3.5 mb-3.5">
                    <div
                      className={`flex h-11 w-11 items-center justify-center rounded-xl ${feat.iconBg}`}
                    >
                      <Icon size={22} />
                    </div>
                    <div>
                      <h3 className="text-lg font-bold text-[var(--foreground)] leading-snug">
                        {feat.title}
                      </h3>
                      <p className="text-xs font-medium text-[var(--muted-foreground)]">
                        {feat.tagline}
                      </p>
                    </div>
                  </div>
                  <p className="text-sm text-[var(--foreground)]/80 leading-relaxed mt-2">
                    {feat.description}
                  </p>
                </div>
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
