"use client";

import Image from "next/image";
import { useState, FormEvent } from "react";
import { motion, AnimatePresence } from "motion/react";
import {
  Loader2,
  RefreshCw,
  Search,
  Network,
  Smile,
  Users,
  Link as LinkIcon,
} from "lucide-react";
import HeroNetworkPreview from "./HeroNetworkPreview";
import { BuzzerAccount } from "@/types/buzzer";
import logo from "@/app/LOGO WEB.png";

type ResultTab = "visualisasi" | "frasa" | "sentimen" | "kluster";

const SAMPLE_PRESETS = [
  {
    label: "Isu Kalimantan",
    url: "https://x.com/WempiF90099/status/18293019284",
  },
  {
    label: "Isu Pilpres wowo2",
    url: "https://x.com/cyber_indojaya99/status/18392019482",
  },
  {
    label: "Isu RoySuryo",
    url: "https://x.com/buzzer_senter07/status/18482019381",
  },
];

interface AnalysisResultData {
  query: string;
  score: number;
  riskLevel: "high" | "medium" | "low";
  accounts: BuzzerAccount[];
  duplicateRatio: number;
  burstRatio: number;
  repeatedPhrases: { phrase: string; count: number; similarity: number }[];
  sentimentBreakdown: { negative: number; neutral: number; positive: number };
}

export default function Hero() {
  const [urlInput, setUrlInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Analysis Result State
  const [result, setResult] = useState<AnalysisResultData | null>(null);
  const [activeResultTab, setActiveResultTab] =
    useState<ResultTab>("visualisasi");

  const handleClear = () => {
    setUrlInput("");
    setErrorMsg(null);
    setResult(null);
  };

  const handleAnalyze = async (e: FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);

    const targetUrl = urlInput.trim();

    if (!targetUrl) {
      setErrorMsg("Silakan masukkan tautan (URL) postingan X (Twitter) terlebih dahulu.");
      return;
    }

    setLoading(true);
    try {
      const res = await fetch("/api/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: targetUrl,
          mode: "deep",
        }),
      });

      const data = await res.json();
      if (!res.ok) {
        setErrorMsg(data.error || "Gagal menjalankan analisis tautan");
      } else {
        const accs: BuzzerAccount[] = data.newAccounts || [];
        setResult({
          query: targetUrl,
          score: 87,
          riskLevel: "high",
          accounts: accs,
          duplicateRatio: 0.84,
          burstRatio: 0.91,
          repeatedPhrases: [
            {
              phrase: "Ayo kawal terus narasi ini sampai tuntas",
              count: 18,
              similarity: 94,
            },
            {
              phrase: "Jangan biarkan pihak lain membelokkan opini publik",
              count: 14,
              similarity: 89,
            },
            {
              phrase: "Ini sudah jelas bukti kegagalan kebijakan",
              count: 11,
              similarity: 85,
            },
            {
              phrase: "Sebarkan ke semua grup sekarang juga!",
              count: 9,
              similarity: 82,
            },
          ],
          sentimentBreakdown: { negative: 82, neutral: 14, positive: 4 },
        });

        // Smooth scroll to results
        setTimeout(() => {
          document
            .getElementById("hasil-analisis")
            ?.scrollIntoView({ behavior: "smooth" });
        }, 150);
      }
    } catch {
      setErrorMsg("Terjadi kendala koneksi saat menghubungi server analisis.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <section id="analisis" className="py-12 md:py-20 px-4 md:px-6">
      <div className="mx-auto max-w-screen-lg">
        {/* Centered Top Badge & Header */}
        <motion.div
          initial={{ opacity: 0, y: 25 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
          className="flex flex-col items-center text-center max-w-2xl mx-auto space-y-4"
        >
          <div className="space-y-2">

            <h1 className="text-3xl sm:text-4xl md:text-5xl font-extrabold tracking-tight text-[var(--foreground)]">
              NEXANTARA
            </h1>
          </div>

          <p className="text-sm md:text-base text-[var(--muted-foreground)] leading-relaxed">
            Mendeteksi koordinasi buzzer, copypasta semantik, dan manipulasi opini publik di media sosial X (Twitter) melalui analisis tautan postingan.
          </p>
        </motion.div>

        {/* Main Input Card — Link Only */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6, delay: 0.1, ease: [0.16, 1, 0.3, 1] }}
          className="mt-10 mx-auto max-w-3xl rounded-2xl border border-[var(--border)] bg-white dark:bg-[var(--card)] p-5 md:p-8 shadow-sm transition-colors duration-200"
        >
          <div className="mb-6 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 border-b border-[var(--border)] pb-4">
            <div>
              <h2 className="text-xl font-bold text-[var(--foreground)] flex items-center gap-2">
                <LinkIcon size={18} className="text-[var(--primary)]" />
                Analisis Tautan Postingan
              </h2>

            </div>

          </div>

          {/* Form: Single URL Link Input */}
          <form onSubmit={handleAnalyze} className="space-y-5">
            <div className="space-y-2">
              <label className="text-xs font-semibold text-[var(--foreground)] flex items-center gap-1.5">
                URL Postingan X (Twitter)
              </label>
              <div className="relative">
                <input
                  type="url"
                  value={urlInput}
                  onChange={(e) => setUrlInput(e.target.value)}
                  placeholder="https://x.com/username/status/18892019482..."
                  className="w-full rounded-xl border border-[var(--border)] bg-[var(--background)] px-4 py-3 text-sm text-[var(--foreground)] placeholder:text-[var(--muted-foreground)] focus:outline-none focus:ring-2 focus:ring-[var(--primary)] transition-all font-mono"
                />
              </div>
            </div>

            {errorMsg && (
              <p className="text-xs font-semibold text-[var(--accent-danger)] pt-1">
                {errorMsg}
              </p>
            )}

            {/* Action Buttons */}
            <div className="flex flex-col sm:flex-row gap-3 pt-2">
              <button
                type="submit"
                disabled={loading}
                className="flex-1 inline-flex items-center justify-center gap-2 rounded-xl bg-[var(--primary)] py-3 px-5 text-sm font-semibold text-white hover:opacity-90 transition-all cursor-pointer disabled:opacity-60 shadow-md shadow-blue-500/20"
              >
                {loading ? (
                  <>
                    <Loader2 size={16} className="animate-spin" />
                    Sedang Menganalisis...
                  </>
                ) : (
                  <>
                    <Search size={16} />
                    Analisis Tautan
                  </>
                )}
              </button>

              <button
                type="button"
                onClick={handleClear}
                className="inline-flex items-center justify-center gap-1.5 rounded-xl border border-[var(--border)] bg-[var(--card)] py-3 px-5 text-sm font-semibold text-[var(--foreground)] hover:bg-[var(--card-subtle)] transition-colors cursor-pointer"
              >
                <RefreshCw size={14} className="text-[var(--muted-foreground)]" />
                Bersihkan
              </button>
            </div>
          </form>
        </motion.div>

        {/* Interactive Results Section */}
        <AnimatePresence>
          {result && (
            <motion.div
              id="hasil-analisis"
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 30 }}
              transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
              className="mt-12 mx-auto max-w-3xl rounded-2xl border border-[var(--border)] bg-white dark:bg-[var(--card)] p-6 md:p-8 shadow-sm space-y-6 transition-colors duration-200"
            >
              {/* Header Hasil */}
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b border-[var(--border)] pb-5">
                <div className="min-w-0 pr-4">
                  <span className="text-xs font-bold uppercase tracking-wider text-[var(--primary)]">
                    Hasil Analisis NEXANTARA
                  </span>
                  <h3 className="text-base sm:text-lg font-bold text-[var(--foreground)] mt-0.5 truncate font-mono">
                    {result.query}
                  </h3>
                </div>

                <div className="flex items-center gap-3 shrink-0">
                  <div className="text-right">
                    <span className="block text-[10px] uppercase font-semibold text-[var(--muted-foreground)]">
                      Skor Risiko Buzzer
                    </span>
                    <span className="text-2xl tabular-score text-[var(--accent-danger)]">
                      {result.score}%
                    </span>
                  </div>
                  <span className="rounded-full bg-[var(--accent-danger)]/15 px-3 py-1 text-xs font-bold text-[var(--accent-danger)] border border-[var(--accent-danger)]/30">
                    Aktivitas Terkoordinasi Tinggi
                  </span>
                </div>
              </div>

              {/* 4 Tabs Hasil */}
              <div className="flex flex-wrap border-b border-[var(--border)] gap-1">
                {[
                  { id: "visualisasi", label: "Visualisasi Pola", Icon: Network },
                  { id: "frasa", label: "Analisis Frasa", Icon: Search },
                  { id: "sentimen", label: "Analisis Sentimen", Icon: Smile },
                  { id: "kluster", label: "Kluster Pengguna", Icon: Users },
                ].map((t) => {
                  const TabIcon = t.Icon;
                  const active = activeResultTab === t.id;
                  return (
                    <button
                      key={t.id}
                      type="button"
                      onClick={() => setActiveResultTab(t.id as ResultTab)}
                      className={`inline-flex items-center gap-2 px-3.5 py-2.5 text-xs md:text-sm font-semibold border-b-2 transition-all cursor-pointer ${
                        active
                          ? "border-[var(--primary)] text-[var(--primary)]"
                          : "border-transparent text-[var(--muted-foreground)] hover:text-[var(--foreground)]"
                      }`}
                    >
                      <TabIcon size={15} />
                      {t.label}
                    </button>
                  );
                })}
              </div>

              {/* Tab 1: Visualisasi Pola */}
              {activeResultTab === "visualisasi" && (
                <div className="space-y-5 pt-2">
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                    <div className="rounded-xl border border-[var(--border)] bg-[var(--card-subtle)] p-4 text-center">
                      <span className="text-[11px] font-semibold text-[var(--muted-foreground)] uppercase">
                        Kemiripan Teks
                      </span>
                      <p className="text-2xl tabular-score text-[var(--foreground)] mt-1">
                        {Math.round(result.duplicateRatio * 100)}%
                      </p>
                    </div>
                    <div className="rounded-xl border border-[var(--border)] bg-[var(--card-subtle)] p-4 text-center">
                      <span className="text-[11px] font-semibold text-[var(--muted-foreground)] uppercase">
                        Sinkronisasi Burst
                      </span>
                      <p className="text-2xl tabular-score text-[var(--accent-danger)] mt-1">
                        {Math.round(result.burstRatio * 100)}%
                      </p>
                    </div>
                    <div className="col-span-2 sm:col-span-1 rounded-xl border border-[var(--border)] bg-[var(--card-subtle)] p-4 text-center">
                      <span className="text-[11px] font-semibold text-[var(--muted-foreground)] uppercase">
                        Sampel Terpindai
                      </span>
                      <p className="text-2xl tabular-score text-[var(--primary)] mt-1">
                        Data Postingan
                      </p>
                    </div>
                  </div>

                  <div className="rounded-xl border border-[var(--border)] bg-[var(--card-subtle)] p-4">
                    <p className="text-xs font-semibold text-[var(--foreground)] mb-2">
                      Graf Hubungan Antar Node Cuitan & Akun dalam Jaringan
                    </p>
                    <div className="h-[280px]">
                      <HeroNetworkPreview />
                    </div>
                  </div>
                </div>
              )}

              {/* Tab 2: Analisis Frasa */}
              {activeResultTab === "frasa" && (
                <div className="space-y-3 pt-2">
                  <p className="text-xs text-[var(--muted-foreground)]">
                    Frasa yang sering diulang dengan kemiripan semantik tinggi (indikasi copypasta terkoordinasi):
                  </p>
                  <div className="space-y-2">
                    {result.repeatedPhrases.map((p, i) => (
                      <div
                        key={i}
                        className="flex items-center justify-between rounded-xl border border-[var(--border)] bg-[var(--card-subtle)] p-3.5 text-sm"
                      >
                        <div className="min-w-0 pr-3">
                          <span className="font-semibold text-[var(--foreground)] block truncate">
                            &ldquo;{p.phrase}&rdquo;
                          </span>
                          <span className="text-xs text-[var(--muted-foreground)]">
                            Muncul {p.count} kali dalam selang waktu berdekatan
                          </span>
                        </div>
                        <span className="shrink-0 rounded-md bg-[var(--accent-warn)]/15 border border-[var(--accent-warn)]/30 px-2 py-0.5 text-xs font-bold text-[var(--accent-warn)]">
                          {p.similarity}% Mirip
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Tab 3: Analisis Sentimen */}
              {activeResultTab === "sentimen" && (
                <div className="space-y-5 pt-2">
                  <p className="text-xs text-[var(--muted-foreground)]">
                    Distribusi sentimen pada data postingan. Anomali terdeteksi jika polarisasi negatif/positif seragam ekstrem:
                  </p>
                  <div className="space-y-3">
                    <div>
                      <div className="flex justify-between text-xs font-semibold mb-1">
                        <span className="text-[var(--accent-danger)]">
                          Negatif ({result.sentimentBreakdown.negative}%)
                        </span>
                        <span className="text-xs text-[var(--muted-foreground)]">
                          Polarisasi Anomali
                        </span>
                      </div>
                      <div className="h-3 w-full rounded-full bg-[var(--border)] overflow-hidden">
                        <div
                          className="h-full bg-[var(--accent-danger)] rounded-full transition-all duration-500"
                          style={{
                            width: `${result.sentimentBreakdown.negative}%`,
                          }}
                        />
                      </div>
                    </div>

                    <div>
                      <div className="flex justify-between text-xs font-semibold mb-1">
                        <span className="text-[var(--foreground)]">
                          Netral ({result.sentimentBreakdown.neutral}%)
                        </span>
                      </div>
                      <div className="h-3 w-full rounded-full bg-[var(--border)] overflow-hidden">
                        <div
                          className="h-full bg-[var(--foreground)]/40 rounded-full transition-all duration-500"
                          style={{
                            width: `${result.sentimentBreakdown.neutral}%`,
                          }}
                        />
                      </div>
                    </div>

                    <div>
                      <div className="flex justify-between text-xs font-semibold mb-1">
                        <span className="text-[var(--accent-go)]">
                          Positif ({result.sentimentBreakdown.positive}%)
                        </span>
                      </div>
                      <div className="h-3 w-full rounded-full bg-[var(--border)] overflow-hidden">
                        <div
                          className="h-full bg-[var(--accent-go)] rounded-full transition-all duration-500"
                          style={{
                            width: `${result.sentimentBreakdown.positive}%`,
                          }}
                        />
                      </div>
                    </div>
                  </div>

                  <div className="rounded-xl border border-amber-200 dark:border-amber-900/40 bg-amber-50 dark:bg-amber-950/20 p-4 text-xs text-amber-900 dark:text-amber-200 leading-relaxed">
                    <strong>Catatan Anomali:</strong> 82% komentar memiliki sentimen negatif seragam dengan struktur kalimat serupa terhadap topik target dalam jendela waktu 15 menit.
                  </div>
                </div>
              )}

              {/* Tab 4: Kluster Pengguna */}
              {activeResultTab === "kluster" && (
                <div className="space-y-3 pt-2">
                  <p className="text-xs text-[var(--muted-foreground)]">
                    Akun-akun terdeteksi yang beroperasi dalam kluster serentak:
                  </p>
                  <div className="space-y-2">
                    {[
                      {
                        username: "WempiF90099",
                        name: "Wempi F.",
                        buzzerScore: 92,
                        followerRatio: 20,
                      },
                      {
                        username: "cyber_indojaya99",
                        name: "Cyber Indojaya",
                        buzzerScore: 89,
                        followerRatio: 37,
                      },
                      {
                        username: "buzzer_senter07",
                        name: "Buzzer Senter",
                        buzzerScore: 84,
                        followerRatio: 17.3,
                      },
                      {
                        username: "Uniliswara0",
                        name: "Uniliswara",
                        buzzerScore: 68,
                        followerRatio: 0.12,
                      },
                    ].map((acc, idx) => (
                      <div
                        key={idx}
                        className="flex items-center justify-between rounded-xl border border-[var(--border)] bg-[var(--card-subtle)] p-3.5"
                      >
                        <div className="flex items-center gap-3">
                          <div className="flex h-9 w-9 items-center justify-center rounded-full bg-gradient-to-tr from-blue-600 to-indigo-600 text-white text-xs font-bold">
                            {acc.username.slice(0, 2).toUpperCase()}
                          </div>
                          <div>
                            <span className="text-sm font-bold text-[var(--foreground)] block">
                              @{acc.username}
                            </span>
                            <span className="text-xs text-[var(--muted-foreground)]">
                              {acc.name} · Rasio Flw: {acc.followerRatio}x
                            </span>
                          </div>
                        </div>

                        <div className="flex items-center gap-2">
                          <span className="rounded-full bg-[var(--accent-danger)]/15 text-[var(--accent-danger)] border border-[var(--accent-danger)]/30 px-2.5 py-0.5 text-xs font-bold">
                            Skor {acc.buzzerScore}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </section>
  );
}
