"use client";

import { motion } from "motion/react";
import { Search, Network, Users, Smile } from "lucide-react";

const FEATURES = [
  {
    title: "Deteksi Pola",
    tagline: "Mengidentifikasi pola komentar yang mencurigakan",
    description:
      "Algoritma kami menganalisis struktur kalimat, frasa umum, repetisi semantik IndoBERTweet, dan anomali waktu untuk mendeteksi aktivitas buzzer yang terkoordinasi.",
    Icon: Search,
    iconBg: "bg-blue-50 text-[var(--primary)] border border-blue-100",
  },
  {
    title: "Visualisasi Data",
    tagline: "Melihat pola dengan visualisasi interaktif",
    description:
      "Visualisasi grafik interaktif membantu Anda memahami hubungan antar akun, sentralitas mention/reply, serta mengidentifikasi kluster aktivitas yang mencurigakan.",
    Icon: Network,
    iconBg: "bg-indigo-50 text-indigo-600 border border-indigo-100",
  },
  {
    title: "Analisis Pengguna",
    tagline: "Mengidentifikasi kluster pengguna mencurigakan",
    description:
      "Sistem kami mengelompokkan pengguna berdasarkan pola posting serentak (temporal burst) dan rasio anomali profil untuk memetakan jaringan akun yang dikoordinasikan.",
    Icon: Users,
    iconBg: "bg-emerald-50 text-emerald-600 border border-emerald-100",
  },
  {
    title: "Analisis Sentimen",
    tagline: "Mendeteksi anomali dalam sentimen cuitan",
    description:
      "Analisis sentimen mendeteksi polarisasi ekstrem dan distribusi sentimen yang seragam secara tidak wajar, yang sering kali menjadi indikator utama operasi cyber-troops.",
    Icon: Smile,
    iconBg: "bg-amber-50 text-amber-600 border border-amber-100",
  },
];

export default function AboutUs() {
  return (
    <section id="tentang-kami" className="border-t border-[var(--border)] bg-white py-16 md:py-20">
      <div className="mx-auto max-w-screen-lg px-4 md:px-6">
        <div className="text-center max-w-2xl mx-auto mb-12">
          <h2 className="text-3xl md:text-4xl font-bold tracking-tight text-[var(--foreground)]">
            Tentang Kami
          </h2>
          <p className="mt-3 text-sm md:text-base text-[var(--muted-foreground)] leading-relaxed">
            Alat analisis canggih berbasis AI untuk mendeteksi aktivitas buzzer dan perilaku terkoordinasi di platform media sosial.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {FEATURES.map((feat, idx) => {
            const Icon = feat.Icon;
            return (
              <motion.div
                key={feat.title}
                initial={{ opacity: 0, y: 16 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.35, delay: idx * 0.08 }}
                className="flex flex-col justify-between rounded-xl border border-[var(--border)] bg-[var(--background)] p-6 shadow-xs hover:border-[var(--primary)]/40 hover:shadow-sm transition-all"
              >
                <div>
                  <div className="flex items-center gap-3.5 mb-3">
                    <div className={`flex h-11 w-11 items-center justify-center rounded-xl ${feat.iconBg}`}>
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
                  <p className="text-sm text-[var(--foreground)]/80 leading-relaxed mt-3">
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
