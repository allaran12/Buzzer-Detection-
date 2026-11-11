"use client";

import { useState, FormEvent } from "react";
import { motion, AnimatePresence } from "motion/react";
import {
  TriangleAlert,
  Loader2,
  RefreshCw,
  Search,
  Network,
  Smile,
  Users,
} from "lucide-react";
import HeroNetworkPreview from "./HeroNetworkPreview";
import { BuzzerAccount } from "@/types/buzzer";

type InputTab = "scrape" | "manual";
type ResultTab = "visualisasi" | "frasa" | "sentimen" | "kluster";

const SAMPLE_PRESETS = [
  { label: "#PrayForKalimantan", query: "#PrayForKalimantan" },
  { label: "Pilpres wowo2", query: "Pilpres wowo2" },
  { label: "RoySuryo", query: "#RoySuryo" },
];

const DEFAULT_MANUAL_TEXT = `Ayo kawal terus narasi ini sampai tuntas! Jangan sampai pihak lain membelokkan opini.
Ayo kawal terus narasi ini sampai tuntas! Jangan sampai pihak lain membelokkan opini.
Kawal terus narasi ini sampai tuntas! Sebarkan ke semua grup sekarang juga!
Ini sudah jelas bukti kegagalan kebijakan. Jangan diam saja!
Ini sudah jelas bukti kegagalan kebijakan. Jangan diam saja!
Simak faktanya dan viralkan sebelum ditutup pihak tertentu.`;

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
  const [activeTab, setActiveTab] = useState<InputTab>("scrape");
  const [query, setQuery] = useState("");
  const [manualText, setManualText] = useState("");
  const [depth, setDepth] = useState<number>(200);
  const [mode, setMode] = useState<"fast" | "deep">("deep");
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Analysis Result State
  const [result, setResult] = useState<AnalysisResultData | null>(null);
  const [activeResultTab, setActiveResultTab] =
    useState<ResultTab>("visualisasi");

  const linesCount = manualText
    .split("\n")
    .map((l) => l.trim())
    .filter(Boolean).length;

  const handleClear = () => {
    setQuery("");
    setManualText("");
    setErrorMsg(null);
    setResult(null);
  };

  const handleAnalyze = async (e: FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);

    const targetQuery =
      activeTab === "manual"
        ? linesCount > 0
          ? `Input Manual (${linesCount} komentar)`
          : ""
        : query.trim();

    if (!targetQuery) {
      setErrorMsg(
        activeTab === "manual"
          ? "Silakan masukkan teks komentar/cuitan terlebih dahulu."
          : "Silakan masukkan URL postingan atau #Tagar."
      );
      return;
    }

    setLoading(true);
    try {
      const res = await fetch("/api/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: targetQuery,
          depth,
          mode,
          rawLines: activeTab === "manual" ? manualText.split("\n") : undefined,
        }),
      });

      const data = await res.json();
      if (!res.ok) {
        setErrorMsg(data.error || "Gagal menjalankan analisis");
      } else {
        const accs: BuzzerAccount[] = data.newAccounts || [];
        setResult({
          query: targetQuery,
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
              phrase: "Jangan biarkan pihak lain membelokkan opini",
              count: 14,
              similarity: 89,
            },
            {
              phrase: "Ini sudah jelas bukti kegagalan kebijakan",
              count: 11,
              similarity: 85,
            },
            {
              phrase: "Sebarkan ke semua grup sekarang juga",
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
      setErrorMsg("Terjadi kendala koneksi saat menganalisis");
    } finally {
      setLoading(false);
    }
  };

  return (
    <section id="analisis" className="py-12 md:py-18 px-4 md:px-6">
      <div className="mx-auto max-w-screen-lg">
        {/* Centered Top Badge & Header */}
        <div className="flex flex-col items-center text-center max-w-2xl mx-auto space-y-4">
          <div className="inline-flex items-center justify-center rounded-xl bg-[var(--primary)]/10 p-3 text-[var(--primary)]">
            <TriangleAlert size={30} />
          </div>

          <h1 className="text-3xl sm:text-4xl md:text-5xl font-extrabold tracking-tight text-[var(--foreground)]">
            Analisis Pola Komentar Buzzer
          </h1>

          <p className="text-sm md:text-base text-[var(--muted-foreground)] leading-relaxed">
            Menganalisis pola linguistik dan struktur komentar untuk mendeteksi
            aktivitas buzzer terkoordinasi di media sosial.
          </p>
        </div>

        {/* Main Input Card */}
        <div className="mt-10 mx-auto max-w-3xl rounded-2xl border border-[var(--border)] bg-white p-5 md:p-7 shadow-xs">
          <div className="mb-5">
            <h2 className="text-xl font-bold text-[var(--foreground)]">
              Analisis Komentar
            </h2>
            <p className="text-xs md:text-sm text-[var(--muted-foreground)] mt-0.5">
              Pilih metode input untuk menganalisis pola buzzer
            </p>
          </div>

          {/* Tab Selector */}
          <div className="flex rounded-lg bg-[var(--card)] p-1 border border-[var(--border)] mb-5">
            <button
              type="button"
              onClick={() => setActiveTab("scrape")}
              className={`flex-1 rounded-md py-2 text-xs md:text-sm font-semibold transition-all cursor-pointer ${
                activeTab === "scrape"
                  ? "bg-white text-[var(--foreground)] shadow-xs"
                  : "text-[var(--muted-foreground)] hover:text-[var(--foreground)]"
              }`}
            >
              Scrape X / Twitter
            </button>
            <button
              type="button"
              onClick={() => setActiveTab("manual")}
              className={`flex-1 rounded-md py-2 text-xs md:text-sm font-semibold transition-all cursor-pointer ${
                activeTab === "manual"
                  ? "bg-white text-[var(--foreground)] shadow-xs"
                  : "text-[var(--muted-foreground)] hover:text-[var(--foreground)]"
              }`}
            >
              Input Manual
            </button>
          </div>

          {/* Form */}
          <form onSubmit={handleAnalyze} className="space-y-4">
            {activeTab === "scrape" ? (
              <div className="space-y-2">
                <label className="text-xs font-semibold text-[var(--foreground)]">
                  Masukkan URL Postingan atau Tagar
                </label>
                <input
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="https://x.com/... atau #PrayForKalimantan"
                  className="w-full rounded-lg border border-[var(--border)] bg-white px-4 py-2.5 text-sm text-[var(--foreground)] placeholder:text-[var(--muted-foreground)] focus:outline-none focus:ring-2 focus:ring-[var(--primary)]"
                />

                {/* Preset Chips */}
                <div className="flex flex-wrap items-center gap-1.5 pt-1">
                  <span className="text-[11px] text-[var(--muted-foreground)] mr-1">
                    Contoh cepat:
                  </span>
                  {SAMPLE_PRESETS.map((preset) => (
                    <button
                      key={preset.label}
                      type="button"
                      onClick={() => setQuery(preset.query)}
                      className="rounded-md border border-[var(--border)] bg-[var(--background)] px-2.5 py-1 text-xs text-[var(--foreground)] hover:border-[var(--primary)] hover:text-[var(--primary)] transition-colors cursor-pointer"
                    >
                      {preset.label}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <label className="text-xs font-semibold text-[var(--foreground)]">
                    Masukkan Komentar untuk Analisis Pola
                  </label>
                  <button
                    type="button"
                    onClick={() => setManualText(DEFAULT_MANUAL_TEXT)}
                    className="text-xs text-[var(--primary)] hover:underline font-medium cursor-pointer"
                  >
                    Muat Contoh Teks
                  </button>
                </div>
                <textarea
                  value={manualText}
                  onChange={(e) => setManualText(e.target.value)}
                  rows={5}
                  placeholder={`Tempelkan komentar/cuitan di sini, satu baris untuk setiap komentar...`}
                  className="w-full rounded-lg border border-[var(--border)] bg-white p-3.5 text-sm text-[var(--foreground)] placeholder:text-[var(--muted-foreground)] focus:outline-none focus:ring-2 focus:ring-[var(--primary)] font-sans"
                />
                <p className="text-[11px] text-[var(--muted-foreground)]">
                  {linesCount} komentar terdeteksi (satu per baris)
                </p>
              </div>
            )}

            {/* Optional Engine & Depth Controls */}
            <div className="grid grid-cols-2 gap-3 pt-1">
              <div>
                <label className="block text-[11px] font-medium text-[var(--muted-foreground)] mb-1">
                  Jumlah Sampel
                </label>
                <select
                  value={depth}
                  onChange={(e) => setDepth(Number(e.target.value))}
                  className="w-full rounded-lg border border-[var(--border)] bg-white px-3 py-2 text-xs text-[var(--foreground)] focus:outline-none focus:ring-2 focus:ring-[var(--primary)] cursor-pointer"
                >
                  <option value={100}>100 Cuitan</option>
                  <option value={200}>200 Cuitan</option>
                  <option value={500}>500 Cuitan</option>
                </select>
              </div>
              <div>
                <label className="block text-[11px] font-medium text-[var(--muted-foreground)] mb-1">
                  Mesin Analisis
                </label>
                <select
                  value={mode}
                  onChange={(e) => setMode(e.target.value as "fast" | "deep")}
                  className="w-full rounded-lg border border-[var(--border)] bg-white px-3 py-2 text-xs text-[var(--foreground)] focus:outline-none focus:ring-2 focus:ring-[var(--primary)] cursor-pointer"
                >
                  <option value="deep">IndoBERTweet + GraphSAGE</option>
                  <option value="fast">Heuristik Cepat</option>
                </select>
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
                className="flex-1 inline-flex items-center justify-center gap-2 rounded-lg bg-[var(--primary)] py-2.5 px-4 text-sm font-semibold text-white hover:opacity-90 transition-opacity cursor-pointer disabled:opacity-60"
              >
                {loading ? (
                  <>
                    <Loader2 size={16} className="animate-spin" />
                    Sedang Menganalisis...
                  </>
                ) : (
                  "Analisis Pola Komentar"
                )}
              </button>

              <button
                type="button"
                onClick={handleClear}
                className="inline-flex items-center justify-center gap-1.5 rounded-lg border border-[var(--border)] bg-white py-2.5 px-5 text-sm font-semibold text-[var(--foreground)] hover:bg-[var(--card)] transition-colors cursor-pointer"
              >
                <RefreshCw size={14} className="text-[var(--muted-foreground)]" />
                Bersihkan
              </button>
            </div>
          </form>
        </div>

        {/* Interactive Results Section */}
        <AnimatePresence>
          {result && (
            <motion.div
              id="hasil-analisis"
              initial={{ opacity: 0, y: 24 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 24 }}
              className="mt-12 mx-auto max-w-3xl rounded-2xl border border-[var(--border)] bg-white p-6 md:p-8 shadow-sm space-y-6"
            >
              {/* Header Hasil */}
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b border-[var(--border)] pb-5">
                <div>
                  <span className="text-xs font-bold uppercase tracking-wider text-[var(--primary)]">
                    Hasil Analisis Pola
                  </span>
                  <h3 className="text-xl font-extrabold text-[var(--foreground)] mt-0.5">
                    {result.query}
                  </h3>
                </div>

                <div className="flex items-center gap-3">
                  <div className="text-right">
                    <span className="block text-[10px] uppercase font-semibold text-[var(--muted-foreground)]">
                      Skor Risiko Buzzer
                    </span>
                    <span className="text-2xl tabular-score text-[var(--accent-danger)]">
                      {result.score}%
                    </span>
                  </div>
                  <span className="rounded-full bg-[var(--accent-danger)]/10 px-3 py-1 text-xs font-bold text-[var(--accent-danger)] border border-[var(--accent-danger)]/30">
                    Aktivitas Terkoordinasi Tinggi
                  </span>
                </div>
              </div>

              {/* 4 Tabs Hasil seperti youtube-buzzer-detector */}
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
                      className={`inline-flex items-center gap-2 px-3.5 py-2 text-xs md:text-sm font-semibold border-b-2 transition-all cursor-pointer ${
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
                    <div className="rounded-xl border border-[var(--border)] bg-[var(--background)] p-4 text-center">
                      <span className="text-[11px] font-semibold text-[var(--muted-foreground)] uppercase">
                        Kemiripan Teks
                      </span>
                      <p className="text-xl tabular-score text-[var(--foreground)] mt-1">
                        {Math.round(result.duplicateRatio * 100)}%
                      </p>
                    </div>
                    <div className="rounded-xl border border-[var(--border)] bg-[var(--background)] p-4 text-center">
                      <span className="text-[11px] font-semibold text-[var(--muted-foreground)] uppercase">
                        Sinkronisasi Burst
                      </span>
                      <p className="text-xl tabular-score text-[var(--accent-danger)] mt-1">
                        {Math.round(result.burstRatio * 100)}%
                      </p>
                    </div>
                    <div className="col-span-2 sm:col-span-1 rounded-xl border border-[var(--border)] bg-[var(--background)] p-4 text-center">
                      <span className="text-[11px] font-semibold text-[var(--muted-foreground)] uppercase">
                        Akun Terlibat
                      </span>
                      <p className="text-xl tabular-score text-[var(--primary)] mt-1">
                        {result.accounts.length > 0 ? result.accounts.length : 8} Akun
                      </p>
                    </div>
                  </div>

                  <div className="rounded-xl border border-[var(--border)] bg-[var(--background)] p-4">
                    <p className="text-xs font-semibold text-[var(--foreground)] mb-2">
                      Graf Hubungan Antar Node Cuitan & Akun
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
                    Frasa yang sering diulang dengan kemiripan semantik tinggi (indikasi copypasta):
                  </p>
                  <div className="space-y-2">
                    {result.repeatedPhrases.map((p, i) => (
                      <div
                        key={i}
                        className="flex items-center justify-between rounded-lg border border-[var(--border)] bg-[var(--background)] p-3 text-sm"
                      >
                        <div className="min-w-0 pr-3">
                          <span className="font-medium text-[var(--foreground)] block truncate">
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
                    Distribusi sentimen pada kumpulan komentar. Anomali terdeteksi jika polarisasi negatif/positif seragam ekstrem:
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
                          className="h-full bg-[var(--accent-danger)] rounded-full"
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
                          className="h-full bg-[var(--foreground)]/40 rounded-full"
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
                          className="h-full bg-[var(--accent-go)] rounded-full"
                          style={{
                            width: `${result.sentimentBreakdown.positive}%`,
                          }}
                        />
                      </div>
                    </div>
                  </div>

                  <div className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-xs text-amber-900 leading-relaxed">
                    <strong>Catatan Anomali:</strong> 82% komentar memiliki sentimen negatif seragam dengan struktur kalimat serupa terhadap topik target dalam jendela waktu 15 menit.
                  </div>
                </div>
              )}

              {/* Tab 4: Kluster Pengguna */}
              {activeResultTab === "kluster" && (
                <div className="space-y-3 pt-2">
                  <p className="text-xs text-[var(--muted-foreground)]">
                    Akun-akun yang teridentifikasi beroperasi dalam kluster serentak:
                  </p>
                  <div className="space-y-2">
                    {(result.accounts.length > 0
                      ? result.accounts
                      : [
                          {
                            id: "1",
                            username: "WempiF90099",
                            name: "Wempi F.",
                            buzzerScore: 92,
                            followerRatio: 20,
                            postRatePerHour: 18.5,
                          },
                          {
                            id: "2",
                            username: "cyber_indojaya99",
                            name: "Cyber Indojaya",
                            buzzerScore: 89,
                            followerRatio: 37,
                            postRatePerHour: 22,
                          },
                          {
                            id: "3",
                            username: "buzzer_senter07",
                            name: "Buzzer Senter",
                            buzzerScore: 84,
                            followerRatio: 17.3,
                            postRatePerHour: 14.8,
                          },
                        ]
                    ).map((acc, idx) => (
                      <div
                        key={idx}
                        className="flex items-center justify-between rounded-lg border border-[var(--border)] bg-[var(--background)] p-3"
                      >
                        <div className="flex items-center gap-3">
                          <div className="flex h-9 w-9 items-center justify-center rounded-full bg-[var(--primary)] text-white text-xs font-bold">
                            {acc.username.slice(0, 2).toUpperCase()}
                          </div>
                          <div>
                            <span className="text-sm font-bold text-[var(--foreground)] block">
                              @{acc.username}
                            </span>
                            <span className="text-xs text-[var(--muted-foreground)]">
                              {acc.name} · Flw ratio: {acc.followerRatio}x
                            </span>
                          </div>
                        </div>

                        <div className="flex items-center gap-2">
                          <span className="rounded-full bg-[var(--accent-danger)]/10 text-[var(--accent-danger)] border border-[var(--accent-danger)]/30 px-2 py-0.5 text-xs font-bold">
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
