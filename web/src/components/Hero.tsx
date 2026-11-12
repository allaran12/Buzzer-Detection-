"use client";

import { FormEvent, useState } from "react";
import { AnimatePresence, motion } from "motion/react";
import { Link as LinkIcon, Loader2, Network, RefreshCw, Search, Smile, Users } from "lucide-react";
import HeroNetworkPreview from "./HeroNetworkPreview";
import { BuzzerAccount } from "@/types/buzzer";

type ResultTab = "visualisasi" | "frasa" | "sentimen" | "kluster";

type NetworkEdge = { source: string; target: string; relationType: string };

type AnalysisResult = {
  query: string;
  score: number;
  riskLevel: "high" | "medium" | "low";
  accounts: BuzzerAccount[];
  scannedPosts: number;
  reviewCount: number;
  source: string;
  modelVersion?: string;
  warnings: string[];
  networkEdges: NetworkEdge[];
  duplicateRatio: number;
  burstRatio: number;
  repeatedPhrases: { phrase: string; count: number; similarity: number }[];
};

function isXPostUrl(value: string): boolean {
  try {
    const url = new URL(value);
    const host = url.hostname.toLowerCase().replace(/^www\./, "");
    return ["http:", "https:"].includes(url.protocol)
      && ["x.com", "twitter.com", "mobile.x.com", "mobile.twitter.com"].includes(host)
      && /\/status\/\d+(?:\/)?$/.test(url.pathname);
  } catch {
    return false;
  }
}

function riskLabel(risk: AnalysisResult["riskLevel"]): string {
  return risk === "high" ? "Risiko Tinggi" : risk === "medium" ? "Perlu Review" : "Risiko Rendah";
}

export default function Hero() {
  const [urlInput, setUrlInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [activeResultTab, setActiveResultTab] = useState<ResultTab>("visualisasi");

  function handleClear() {
    setUrlInput("");
    setErrorMsg(null);
    setResult(null);
  }

  async function handleAnalyze(event: FormEvent) {
    event.preventDefault();
    setErrorMsg(null);
    const targetUrl = urlInput.trim();

    if (!isXPostUrl(targetUrl)) {
      setErrorMsg("Masukkan URL postingan X yang valid, misalnya https://x.com/user/status/123...");
      return;
    }

    setLoading(true);
    try {
      const response = await fetch("/api/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: targetUrl, limit: 25, fetchReplies: true }),
      });
      const data = (await response.json()) as Record<string, unknown>;
      if (!response.ok) {
        setErrorMsg(String(data.error || "Gagal menjalankan analisis tautan"));
        return;
      }

      const accounts = Array.isArray(data.accounts) ? data.accounts as BuzzerAccount[] : [];
      const summary = (data.summary || {}) as Record<string, unknown>;
      const highRisk = Number(summary.high_risk_count || 0);
      const mediumRisk = Number(summary.medium_risk_count || 0);
      setResult({
        query: targetUrl,
        score: Number(summary.average_score || 0),
        riskLevel: highRisk > 0 ? "high" : mediumRisk > 0 ? "medium" : "low",
        accounts,
        scannedPosts: Number(summary.total_posts || 0),
        reviewCount: Number(summary.review_count || 0),
        source: String(data.source || "inference"),
        modelVersion: typeof data.modelVersion === "string" ? data.modelVersion : undefined,
        warnings: Array.isArray(data.warnings) ? data.warnings.filter((value): value is string => typeof value === "string" && value.length > 0) : [],
        networkEdges: Array.isArray(data.networkEdges) ? data.networkEdges as NetworkEdge[] : [],
        duplicateRatio: Number(summary.duplicate_ratio || 0),
        burstRatio: Number(summary.burst_ratio || 0),
        repeatedPhrases: Array.isArray(data.repeatedPhrases) ? data.repeatedPhrases as AnalysisResult["repeatedPhrases"] : [],
      });
      setActiveResultTab("visualisasi");
      window.setTimeout(() => document.getElementById("hasil-analisis")?.scrollIntoView({ behavior: "smooth" }), 150);
    } catch {
      setErrorMsg("Backend analisis tidak dapat dihubungi. Pastikan FastAPI dan akun scraper aktif.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section id="analisis" className="px-4 py-12 md:px-6 md:py-20">
      <div className="mx-auto max-w-screen-lg">
        <motion.div
          initial={{ opacity: 0, y: 25 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
          className="mx-auto flex max-w-2xl flex-col items-center space-y-4 text-center"
        >
          <h1 className="text-3xl font-extrabold tracking-tight text-[var(--foreground)] sm:text-4xl md:text-5xl">NEXANTARA</h1>
          <p className="text-sm leading-relaxed text-[var(--muted-foreground)] md:text-base">
            Memproses URL postingan X dengan IndoBERTweet, Temporal LSTM, dan GraphSAGE untuk menemukan sinyal koordinasi yang dapat ditinjau manusia.
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6, delay: 0.1, ease: [0.16, 1, 0.3, 1] }}
          className="mx-auto mt-10 max-w-3xl rounded-2xl border border-[var(--border)] bg-white p-5 shadow-sm transition-colors duration-200 dark:bg-[var(--card)] md:p-8"
        >
          <div className="mb-6 border-b border-[var(--border)] pb-4">
            <h2 className="flex items-center gap-2 text-xl font-bold text-[var(--foreground)]"><LinkIcon size={18} className="text-[var(--primary)]" />Analisis Tautan Postingan</h2>
            <p className="mt-1 text-xs text-[var(--muted-foreground)]">Sistem mengambil postingan target dan balasan publik yang tersedia melalui akun scraper.</p>
          </div>
          <form onSubmit={handleAnalyze} className="space-y-5">
            <label className="block space-y-2 text-xs font-semibold text-[var(--foreground)]">
              URL Postingan X (Twitter)
              <input
                type="url"
                required
                value={urlInput}
                onChange={(event) => setUrlInput(event.target.value)}
                placeholder="https://x.com/username/status/18892019482..."
                className="w-full rounded-xl border border-[var(--border)] bg-[var(--background)] px-4 py-3 font-mono text-sm text-[var(--foreground)] placeholder:text-[var(--muted-foreground)] transition-all focus:outline-none focus:ring-2 focus:ring-[var(--primary)]"
              />
            </label>
            {errorMsg && <p className="pt-1 text-xs font-semibold text-[var(--accent-danger)]">{errorMsg}</p>}
            <div className="flex flex-col gap-3 pt-2 sm:flex-row">
              <button type="submit" disabled={loading} className="inline-flex flex-1 cursor-pointer items-center justify-center gap-2 rounded-xl bg-[var(--primary)] px-5 py-3 text-sm font-semibold text-white shadow-md shadow-blue-500/20 transition-all hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60">
                {loading ? <><Loader2 size={16} className="animate-spin" />Sedang menganalisis...</> : <><Search size={16} />Analisis Tautan</>}
              </button>
              <button type="button" onClick={handleClear} className="inline-flex cursor-pointer items-center justify-center gap-1.5 rounded-xl border border-[var(--border)] bg-[var(--card)] px-5 py-3 text-sm font-semibold text-[var(--foreground)] transition-colors hover:bg-[var(--card-subtle)]"><RefreshCw size={14} className="text-[var(--muted-foreground)]" />Bersihkan</button>
            </div>
          </form>
        </motion.div>

        <AnimatePresence>
          {result && (
            <motion.div id="hasil-analisis" initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 30 }} className="mx-auto mt-12 max-w-3xl space-y-6 rounded-2xl border border-[var(--border)] bg-white p-6 shadow-sm transition-colors duration-200 dark:bg-[var(--card)] md:p-8">
              <div className="flex flex-col gap-3 border-b border-[var(--border)] pb-5 sm:flex-row sm:items-center sm:justify-between">
                <div className="min-w-0 pr-4"><span className="text-xs font-bold uppercase tracking-wider text-[var(--primary)]">Hasil Analisis NEXANTARA</span><h3 className="mt-0.5 truncate font-mono text-base font-bold text-[var(--foreground)] sm:text-lg">{result.query}</h3><p className="mt-1 text-[10px] text-[var(--muted-foreground)]">{result.source}{result.modelVersion ? ` · ${result.modelVersion}` : ""}</p></div>
                <div className="flex shrink-0 items-center gap-3"><div className="text-right"><span className="block text-[10px] font-semibold uppercase text-[var(--muted-foreground)]">Skor Risiko Buzzer</span><span className="tabular-score text-2xl text-[var(--accent-danger)]">{result.score.toFixed(2)}%</span></div><span className={`rounded-full border px-3 py-1 text-xs font-bold ${result.riskLevel === "high" ? "border-[var(--accent-danger)]/30 bg-[var(--accent-danger)]/15 text-[var(--accent-danger)]" : result.riskLevel === "medium" ? "border-[var(--accent-warn)]/30 bg-[var(--accent-warn)]/15 text-[var(--accent-warn)]" : "border-[var(--accent-go)]/30 bg-[var(--accent-go)]/15 text-[var(--accent-go)]"}`}>{riskLabel(result.riskLevel)}</span></div>
              </div>

              {result.warnings.length > 0 && <div className="rounded-xl border border-amber-200 bg-amber-50 p-3 text-xs leading-relaxed text-amber-900 dark:border-amber-900/40 dark:bg-amber-950/20 dark:text-amber-200">{result.warnings.map((warning) => <p key={warning}>{warning}</p>)}</div>}

              <div className="flex flex-wrap gap-1 border-b border-[var(--border)]">
                {[
                  { id: "visualisasi", label: "Visualisasi Pola", Icon: Network },
                  { id: "frasa", label: "Analisis Frasa", Icon: Search },
                  { id: "sentimen", label: "Batasan Model", Icon: Smile },
                  { id: "kluster", label: "Akun", Icon: Users },
                ].map(({ id, label, Icon }) => <button key={id} type="button" onClick={() => setActiveResultTab(id as ResultTab)} className={`inline-flex cursor-pointer items-center gap-2 border-b-2 px-3.5 py-2.5 text-xs font-semibold transition-all md:text-sm ${activeResultTab === id ? "border-[var(--primary)] text-[var(--primary)]" : "border-transparent text-[var(--muted-foreground)] hover:text-[var(--foreground)]"}`}><Icon size={15} />{label}</button>)}
              </div>

              {activeResultTab === "visualisasi" && <div className="space-y-5 pt-2"><div className="grid grid-cols-2 gap-3 sm:grid-cols-4"><Metric label="Kemiripan Teks" value={`${Math.round(result.duplicateRatio * 100)}%`} /><Metric label="Sinkronisasi Burst" value={`${Math.round(result.burstRatio * 100)}%`} danger /><Metric label="Post Terpindai" value={String(result.scannedPosts)} primary /><Metric label="Perlu Review" value={String(result.reviewCount)} warning /></div><div className="rounded-xl border border-[var(--border)] bg-[var(--card-subtle)] p-4"><p className="mb-2 text-xs font-semibold text-[var(--foreground)]">Graf relasi yang ditemukan pada sampel live</p><div className="h-[280px]"><HeroNetworkPreview accounts={result.accounts} edges={result.networkEdges} /></div></div></div>}
              {activeResultTab === "frasa" && <div className="space-y-3 pt-2"><p className="text-xs text-[var(--muted-foreground)]">Evidence frasa lintas akun dari sampel yang berhasil dikumpulkan.</p>{result.repeatedPhrases.length === 0 ? <p className="rounded-xl border border-[var(--border)] bg-[var(--card-subtle)] p-4 text-sm text-[var(--muted-foreground)]">Belum ada pasangan frasa dengan evidence kemiripan yang cukup.</p> : result.repeatedPhrases.map((phrase) => <div key={`${phrase.phrase}-${phrase.similarity}`} className="flex items-center justify-between rounded-xl border border-[var(--border)] bg-[var(--card-subtle)] p-3.5 text-sm"><div className="min-w-0 pr-3"><span className="block truncate font-semibold text-[var(--foreground)]">&ldquo;{phrase.phrase}&rdquo;</span><span className="text-xs text-[var(--muted-foreground)]">Terlihat pada minimal {phrase.count} postingan lintas akun</span></div><span className="shrink-0 rounded-md border border-[var(--accent-warn)]/30 bg-[var(--accent-warn)]/15 px-2 py-0.5 text-xs font-bold text-[var(--accent-warn)]">{phrase.similarity}% mirip</span></div>)}</div>}

              {activeResultTab === "sentimen" && <div className="rounded-xl border border-[var(--border)] bg-[var(--card-subtle)] p-4 text-sm leading-relaxed text-[var(--muted-foreground)]">Analisis sentimen tidak dijalankan oleh tiga branch model final. Sistem sengaja tidak menampilkan persentase sentimen buatan; gunakan evidence IndoBERTweet, temporal, dan graph untuk review.</div>}

              {activeResultTab === "kluster" && <div className="space-y-3 pt-2"><p className="text-xs text-[var(--muted-foreground)]">Akun yang muncul dalam hasil live, diurutkan berdasarkan skor fusion.</p>{result.accounts.length === 0 ? <p className="rounded-xl border border-[var(--border)] bg-[var(--card-subtle)] p-4 text-sm text-[var(--muted-foreground)]">Tidak ada akun dari response backend.</p> : result.accounts.map((account) => <div key={account.id} className="flex items-center justify-between rounded-xl border border-[var(--border)] bg-[var(--card-subtle)] p-3.5"><div className="flex min-w-0 items-center gap-3"><div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-gradient-to-tr from-blue-600 to-indigo-600 text-xs font-bold text-white">{account.username.slice(0, 2).toUpperCase()}</div><div className="min-w-0"><span className="block truncate text-sm font-bold text-[var(--foreground)]">@{account.username}</span><span className="text-xs text-[var(--muted-foreground)]">{account.explanation || "Tidak ada evidence dominan"}</span></div></div><span className="shrink-0 rounded-full border border-[var(--accent-danger)]/30 bg-[var(--accent-danger)]/15 px-2.5 py-0.5 text-xs font-bold text-[var(--accent-danger)]">{account.buzzerScore.toFixed(1)}</span></div>)}</div>}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </section>
  );
}

function Metric({ label, value, danger, primary, warning }: { label: string; value: string; danger?: boolean; primary?: boolean; warning?: boolean }) {
  const color = danger ? "text-[var(--accent-danger)]" : primary ? "text-[var(--primary)]" : warning ? "text-[var(--accent-warn)]" : "text-[var(--foreground)]";
  return <div className="rounded-xl border border-[var(--border)] bg-[var(--card-subtle)] p-4 text-center"><span className="text-[11px] font-semibold uppercase text-[var(--muted-foreground)]">{label}</span><p className={`tabular-score mt-1 text-2xl ${color}`}>{value}</p></div>;
}
