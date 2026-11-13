"use client";

import Image from "next/image";
import { FormEvent, useMemo, useState } from "react";
import { AnimatePresence, motion } from "motion/react";
import {
  Activity,
  AlertTriangle,
  BarChart3,
  ChevronDown,
  Clock3,
  FileSearch,
  HeartPulse,
  Loader2,
  Network,
  RefreshCw,
  Search,
  Users,
} from "lucide-react";
import HeroNetworkPreview from "./HeroNetworkPreview";
import { BuzzerAccount } from "@/types/buzzer";

type ResultTab = "overview" | "network" | "sentiment" | "evidence" | "accounts";
type QueryKind = "post" | "hashtag" | "search" | "keyword";

type NetworkNode = {
  id: string;
  username: string;
  name?: string;
  avatar?: string;
  role?: "account" | "target";
  isHub?: boolean;
  isTargetOnly?: boolean;
  buzzerScore?: number;
  riskLevel?: "high" | "medium" | "low";
  inDegree?: number;
  outDegree?: number;
  degree?: number;
  componentSize?: number;
};

type NetworkEdge = {
  source: string;
  target: string;
  relationType: string;
  relationTypes?: string[];
  count?: number;
};

type SentimentSummary = {
  method: string;
  disclaimer: string;
  total_posts: number;
  counts: Record<string, number>;
  percentages: Record<string, number>;
  average_score: number;
  dominant: "positive" | "negative" | "neutral" | "mixed";
  examples: Array<{ label: string; score: number; username: string; text: string }>;
};

type AnalysisResult = {
  query: string;
  score: number;
  riskLevel: "high" | "medium" | "low";
  accounts: BuzzerAccount[];
  scannedPosts: number;
  reviewCount: number;
  source: string;
  warnings: string[];
  networkNodes: NetworkNode[];
  networkEdges: NetworkEdge[];
  graph: Record<string, unknown>;
  sentiment: SentimentSummary;
  duplicateRatio: number;
  burstRatio: number;
  repeatedPhrases: Array<{ phrase: string; count: number; accountCount?: number; similarity?: number }>;
  evidence: Record<string, unknown>;
};

type JsonRecord = Record<string, unknown>;

function asRecord(value: unknown): JsonRecord {
  return value && typeof value === "object" && !Array.isArray(value) ? value as JsonRecord : {};
}

function asArray(value: unknown): unknown[] {
  return Array.isArray(value) ? value : [];
}

function numeric(value: unknown, fallback = 0): number {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
}

function deriveSentiment(accounts: BuzzerAccount[]): SentimentSummary {
  const counts: Record<string, number> = { positive: 0, negative: 0, neutral: 0, mixed: 0 };
  const examples: SentimentSummary["examples"] = [];
  let totalScore = 0;
  let totalPosts = 0;
  for (const account of accounts) {
    for (const tweet of account.tweets || []) {
      const label = tweet.sentiment?.label || "neutral";
      counts[label] = (counts[label] || 0) + 1;
      totalScore += numeric(tweet.sentiment?.score);
      totalPosts += 1;
      if (examples.length < 8) examples.push({ label, score: numeric(tweet.sentiment?.score), username: account.username, text: tweet.text });
    }
  }
  const percentages = Object.fromEntries(Object.entries(counts).map(([label, count]) => [label, totalPosts ? Math.round((count / totalPosts) * 1000) / 10 : 0]));
  const dominant = (Object.entries(counts).sort((first, second) => second[1] - first[1])[0]?.[0] || "neutral") as SentimentSummary["dominant"];
  return {
    method: "account-tweet-fallback",
    disclaimer: "Sentimen diturunkan dari detail tweet karena backend tidak mengirim ringkasan sentimen.",
    total_posts: totalPosts,
    counts,
    percentages,
    average_score: totalPosts ? totalScore / totalPosts : 0,
    dominant,
    examples,
  };
}

function normalizeSentiment(value: unknown, accounts: BuzzerAccount[]): SentimentSummary {
  const source = asRecord(value);
  const fallback = deriveSentiment(accounts);
  const counts = Object.fromEntries(Object.entries({ ...fallback.counts, ...asRecord(source.counts) }).map(([label, count]) => [label, numeric(count)]));
  const percentages = Object.fromEntries(Object.entries({ ...fallback.percentages, ...asRecord(source.percentages) }).map(([label, percentage]) => [label, numeric(percentage)]));
  const examples = asArray(source.examples).filter((item): item is JsonRecord => Boolean(item && typeof item === "object" && !Array.isArray(item))).map((item) => ({
    label: String(item.label || "neutral"),
    score: numeric(item.score),
    username: String(item.username || "unknown"),
    text: String(item.text || ""),
  }));
  return {
    method: String(source.method || fallback.method),
    disclaimer: String(source.disclaimer || fallback.disclaimer),
    total_posts: numeric(source.total_posts ?? source.totalPosts, fallback.total_posts),
    counts,
    percentages,
    average_score: numeric(source.average_score ?? source.averageScore, fallback.average_score),
    dominant: String(source.dominant || fallback.dominant) as SentimentSummary["dominant"],
    examples: examples.length ? examples : fallback.examples,
  };
}

function deriveNetwork(accounts: BuzzerAccount[]): { nodes: NetworkNode[]; edges: NetworkEdge[] } {
  const nodes = new Map<string, NetworkNode>();
  const edges = new Map<string, NetworkEdge>();
  for (const account of accounts) {
    nodes.set(account.id, {
      id: account.id,
      username: account.username,
      name: account.name,
      avatar: account.avatar,
      role: "account",
      buzzerScore: account.buzzerScore,
      riskLevel: account.riskLevel,
      inDegree: account.inDegree,
      outDegree: account.outDegree,
      degree: account.totalDegree ?? ((account.inDegree || 0) + (account.outDegree || 0)),
      componentSize: account.componentSize,
    });
    for (const tweet of account.tweets || []) {
      if (!tweet.targetUsername || tweet.relationType === "original") continue;
      const targetId = tweet.targetPostId ? `post:${tweet.targetPostId}` : `target:${tweet.targetUsername}`;
      if (!nodes.has(targetId)) nodes.set(targetId, { id: targetId, username: tweet.targetUsername, role: "target", isTargetOnly: true, riskLevel: "low" });
      const key = `${account.id}|${targetId}|${tweet.relationType}`;
      const current = edges.get(key);
      edges.set(key, current ? { ...current, count: (current.count || 1) + 1 } : { source: account.id, target: targetId, relationType: tweet.relationType, count: 1 });
    }
  }
  return { nodes: [...nodes.values()], edges: [...edges.values()] };
}

function normalizeNetwork(value: unknown, edgesValue: unknown, accounts: BuzzerAccount[]): { nodes: NetworkNode[]; edges: NetworkEdge[] } {
  const rawNodes = asArray(value).filter((item): item is NetworkNode => Boolean(item && typeof item === "object" && !Array.isArray(item))).map((item) => item as NetworkNode);
  const rawEdges = asArray(edgesValue).filter((item): item is NetworkEdge => Boolean(item && typeof item === "object" && !Array.isArray(item))).map((item) => item as NetworkEdge);
  if (rawNodes.length || rawEdges.length) return { nodes: rawNodes, edges: rawEdges };
  return deriveNetwork(accounts);
}

function deriveRepeatedPhrases(accounts: BuzzerAccount[]): AnalysisResult["repeatedPhrases"] {
  const phrases = new Map<string, { count: number; accounts: Set<string> }>();
  for (const account of accounts) {
    for (const tweet of account.tweets || []) {
      const tokens = tweet.text.toLowerCase().replace(/https?:\/\/\S+/g, "").match(/[\w#@'-]+/g) || [];
      const seen = new Set<string>();
      for (let size = 3; size <= Math.min(6, tokens.length); size += 1) {
        for (let start = 0; start <= tokens.length - size; start += 1) {
          const phrase = tokens.slice(start, start + size).join(" ");
          if (phrase.length < 12 || seen.has(phrase)) continue;
          seen.add(phrase);
          const current = phrases.get(phrase) || { count: 0, accounts: new Set<string>() };
          current.count += 1;
          current.accounts.add(account.id);
          phrases.set(phrase, current);
        }
      }
    }
  }
  return [...phrases.entries()]
    .filter(([, value]) => value.accounts.size >= 2)
    .sort((first, second) => second[1].count - first[1].count)
    .slice(0, 8)
    .map(([phrase, value]) => ({ phrase, count: value.count, accountCount: value.accounts.size, similarity: undefined }));
}

function normalizeEvidence(value: unknown, nodes: NetworkNode[], edges: NetworkEdge[], sentiment: SentimentSummary, repeatedPhrases: AnalysisResult["repeatedPhrases"]): Record<string, unknown> {
  const source = asRecord(value);
  return Object.keys(source).length ? source : {
    topHubs: nodes.filter((node) => node.isHub).slice(0, 5),
    repeatedPhraseCount: repeatedPhrases.length,
    sentimentMethod: sentiment.method,
    validEdgeEvents: edges.reduce((total, edge) => total + numeric(edge.count, 1), 0),
  };
}

function parseQueryKind(value: string): QueryKind | null {
  const trimmed = value.trim();
  if (!trimmed) return null;
  try {
    const url = new URL(trimmed);
    const host = url.hostname.toLowerCase().replace(/^www\./, "");
    if (!trimmed.match(/^https?:\/\//i) || !["x.com", "twitter.com", "mobile.x.com", "mobile.twitter.com"].includes(host)) return null;
    const path = url.pathname.toLowerCase();
    if (/\/status\/\d+(?:\/)?$/.test(path)) return "post";
    if (path.startsWith("/hashtag/") && path.length > 9) return "hashtag";
    if (path === "/search" && (url.searchParams.get("q")?.trim().length ?? 0) >= 2) return "search";
    return null;
  } catch {
    if (/^https?:\/\//i.test(trimmed)) return null;
    if (trimmed.startsWith("#")) return trimmed.slice(1).trim().length >= 2 ? "hashtag" : null;
    return trimmed.length >= 2 ? "keyword" : null;
  }
}

function riskLabel(risk: AnalysisResult["riskLevel"]): string {
  return risk === "high" ? "Risiko tinggi" : risk === "medium" ? "Perlu review" : "Risiko rendah";
}

function riskClass(risk: "high" | "medium" | "low"): string {
  return risk === "high"
    ? "border-red-500/25 bg-red-500/10 text-red-600 dark:text-red-300"
    : risk === "medium"
      ? "border-amber-500/25 bg-amber-500/10 text-amber-700 dark:text-amber-300"
      : "border-emerald-500/25 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300";
}

function sentimentLabel(value: string): string {
  return { positive: "Positif", negative: "Negatif", neutral: "Netral", mixed: "Campuran" }[value] ?? "Netral";
}

function sentimentColor(value: string): string {
  return value === "negative" ? "var(--accent-danger)" : value === "positive" ? "var(--accent-go)" : value === "mixed" ? "var(--accent-warn)" : "var(--primary)";
}

function clampPercentage(value: unknown): number {
  return Math.min(100, Math.max(0, numeric(value)));
}

function formatFollowers(value: unknown): string {
  return new Intl.NumberFormat("id-ID", { notation: "compact", maximumFractionDigits: 1 }).format(Math.max(0, numeric(value)));
}

const signalDefinitions = [
  { key: "indobertweet", label: "Sinyal teks", color: "var(--primary)" },
  { key: "temporal_lstm", label: "Sinyal waktu", color: "var(--accent-warn)" },
  { key: "graphsage", label: "Sinyal relasi", color: "var(--accent-danger)" },
];

function signalValues(accounts: BuzzerAccount[]) {
  const completeAccounts = accounts.filter((account) => signalDefinitions.every(({ key }) => {
    const value = account.branchScores?.[key];
    return typeof value === "number" && Number.isFinite(value);
  }));
  const values = completeAccounts.flatMap((account) => signalDefinitions.map(({ key }) => account.branchScores?.[key] as number));
  const normalized = values.every((value) => value >= 0 && value <= 1);
  const percentages = values.every((value) => value >= 0 && value <= 100);
  if (!completeAccounts.length || (!normalized && !percentages)) return null;
  return { signals: signalDefinitions.map((signal) => ({ ...signal, values: completeAccounts.map((account) => account.branchScores?.[signal.key] as number) })), scale: normalized ? 100 : 1 };
}

function ProfileAvatar({ account, size = 44 }: { account: { username: string; avatar?: string; name?: string }; size?: number }) {
  const [failed, setFailed] = useState(false);
  const source = account.avatar?.trim();
  let allowed = false;
  try {
    const hostname = source ? new URL(source).hostname.toLowerCase() : "";
    allowed = hostname === "pbs.twimg.com" || hostname === "abs.twimg.com";
  } catch {
    allowed = false;
  }
  const initials = (account.name || account.username || "??").replace(/^@/, "").slice(0, 2).toUpperCase();
  return (
    <span className="relative flex shrink-0 items-center justify-center overflow-hidden rounded-full bg-[linear-gradient(135deg,var(--primary),#0f766e)] font-bold text-white" style={{ width: size, height: size, fontSize: Math.max(10, size / 3.1) }}>
      {source && allowed && !failed ? <Image src={source} alt={`Foto profil @${account.username}`} fill sizes={`${size}px`} unoptimized onError={() => setFailed(true)} className="object-cover" /> : initials}
    </span>
  );
}

function Metric({ label, value, tone = "normal", icon: Icon }: { label: string; value: string; tone?: "normal" | "danger" | "primary" | "warning"; icon?: typeof Activity }) {
  const color = tone === "danger" ? "text-[var(--accent-danger)]" : tone === "primary" ? "text-[var(--primary)]" : tone === "warning" ? "text-[var(--accent-warn)]" : "text-[var(--foreground)]";
  return (
    <div className="rounded-2xl border border-[var(--border)] bg-[var(--card-subtle)] p-4">
      <div className="flex items-center justify-between gap-2 text-[10px] font-bold uppercase tracking-[0.13em] text-[var(--muted-foreground)]"><span>{label}</span>{Icon && <Icon size={14} />}</div>
      <p className={`tabular-score mt-2 text-2xl ${color}`}>{value}</p>
    </div>
  );
}

function SentimentBars({ sentiment }: { sentiment: SentimentSummary }) {
  const entries = ["positive", "negative", "neutral", "mixed"];
  const total = numeric(sentiment.total_posts);
  if (total === 0) return <Empty text="Belum ada sampel untuk distribusi sentimen." />;
  return (
    <div className="space-y-3">
      {entries.filter((label) => label !== "mixed" || numeric(sentiment.counts?.[label]) > 0 || numeric(sentiment.percentages?.[label]) > 0).map((label) => {
        const percentage = clampPercentage(sentiment.percentages?.[label]);
        const count = Math.max(0, numeric(sentiment.counts?.[label]));
        return (
          <div key={label}>
            <div className="mb-1 flex items-center justify-between text-xs"><span className="font-semibold text-[var(--foreground)]">{sentimentLabel(label)}</span><span className="tabular-nums text-[var(--muted-foreground)]">{percentage.toFixed(1)}% · {count} sampel</span></div>
            <div className="h-2 overflow-hidden rounded-full bg-[var(--border)]"><div className="h-full rounded-full transition-all" title={`${sentimentLabel(label)}: ${percentage.toFixed(1)}% (${count} sampel)`} style={{ width: `${percentage}%`, backgroundColor: sentimentColor(label) }} /></div>
          </div>
        );
      })}
    </div>
  );
}

export default function Hero() {
  const [queryInput, setQueryInput] = useState("");
  const [limit, setLimit] = useState("500");
  const [fetchReplies, setFetchReplies] = useState(true);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [activeResultTab, setActiveResultTab] = useState<ResultTab>("overview");

  const queryKind = useMemo(() => parseQueryKind(queryInput), [queryInput]);

  function handleClear() {
    setQueryInput("");
    setErrorMsg(null);
    setResult(null);
  }

  async function handleAnalyze(event: FormEvent) {
    event.preventDefault();
    setErrorMsg(null);
    const query = queryInput.trim();
    const kind = parseQueryKind(query);
    if (!kind) {
      setErrorMsg("Masukkan URL posting/hashtag/search X, hashtag seperti #topik, atau keyword minimal 2 karakter.");
      return;
    }
    setLoading(true);
    try {
      const response = await fetch("/api/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query, limit: Number(limit), fetchReplies: kind === "post" ? fetchReplies : false }),
      });
      const data = (await response.json()) as Record<string, unknown>;
      if (!response.ok) {
        setErrorMsg(String(data.error || "Gagal menjalankan analisis"));
        return;
      }
      const summary = (data.summary || {}) as Record<string, unknown>;
      const highRisk = Number(summary.high_risk_count || 0);
      const mediumRisk = Number(summary.medium_risk_count || 0);
      const accounts = asArray(data.accounts) as BuzzerAccount[];
      const network = normalizeNetwork(data.networkNodes ?? data.network_nodes, data.networkEdges ?? data.network_edges, accounts);
      const repeatedPhrases = asArray(data.repeatedPhrases ?? data.repeated_phrases) as AnalysisResult["repeatedPhrases"];
      const resolvedPhrases = repeatedPhrases.length ? repeatedPhrases : deriveRepeatedPhrases(accounts);
      const sentiment = normalizeSentiment(data.sentiment, accounts);
      setResult({
        query,
        score: numeric(summary.average_score),
        riskLevel: highRisk > 0 ? "high" : mediumRisk > 0 ? "medium" : "low",
        accounts,
        scannedPosts: Math.max(0, numeric(summary.total_posts)),
        reviewCount: Number(summary.review_count || 0),
        source: String(data.source || "inference"),

        warnings: Array.isArray(data.warnings) ? data.warnings.filter((value): value is string => typeof value === "string" && value.length > 0) : [],
        networkNodes: network.nodes,
        networkEdges: network.edges,
        graph: (data.graph || {}) as Record<string, unknown>,
        sentiment,
        duplicateRatio: Number(summary.duplicate_ratio || 0),
        burstRatio: Number(summary.burst_ratio || 0),
        repeatedPhrases: resolvedPhrases,
        evidence: normalizeEvidence(data.evidence, network.nodes, network.edges, sentiment, resolvedPhrases),
      });
      setActiveResultTab("overview");
      window.setTimeout(() => document.getElementById("hasil-analisis")?.scrollIntoView({ behavior: "smooth", block: "start" }), 150);
    } catch {
      setErrorMsg("Backend analisis tidak dapat dihubungi. Pastikan FastAPI dan akun scraper aktif.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section id="analisis" className="relative overflow-hidden px-4 py-14 md:px-6 md:py-24">
      <div className="pointer-events-none absolute inset-x-0 top-0 -z-10 h-[430px] bg-[radial-gradient(circle_at_20%_20%,rgba(37,99,235,0.13),transparent_34%),radial-gradient(circle_at_80%_30%,rgba(15,118,110,0.1),transparent_32%)]" />
      <div className="mx-auto max-w-screen-xl">
        <motion.div initial={false} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ duration: 0.6 }} className="mx-auto max-w-3xl text-center">
          <h1 className="mt-3 text-4xl font-extrabold tracking-tight sm:text-5xl md:text-6xl">NEXANTARA</h1>
          <p className="mx-auto mt-5 max-w-2xl text-sm leading-7 text-[var(--muted-foreground)] md:text-base">NEXANTARA membaca sinyal koordinasi dari teks, pola waktu, dan relasi akun pada postingan, hashtag, maupun keyword publik di X. Hasilnya adalah bahan review berbasis data, bukan keputusan otomatis.</p>
        </motion.div>

        <motion.div initial={false} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ duration: 0.6, delay: 0.1 }} className="mx-auto mt-10 max-w-4xl rounded-2xl border border-[var(--border)] bg-[var(--card)] p-5 md:p-8">
          <div className="flex flex-col gap-3 border-b border-[var(--border)] pb-5 md:flex-row md:items-end md:justify-between">
            <div>
              <div className="flex items-center gap-2 text-3xl font-bold text-[var(--foreground)]"><FileSearch size={19} className="text-[var(--primary)]" />Analisis URL X</div>
              <p className="mt-1 text-xs leading-5 text-[var(--muted-foreground)]">Maksimal 500 postingan terbaru.</p>
            </div>
          </div>
          <form onSubmit={handleAnalyze} className="mt-6 space-y-5">
            <label className="block space-y-2 text-xs font-bold text-[var(--foreground)]">URL posting / hashtag / keyword
              <div className="relative"><Search size={17} className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-[var(--muted-foreground)]" /><input type="text" required value={queryInput} onChange={(event) => setQueryInput(event.target.value)} placeholder="https://x.com/user/status/123... atau #topik atau kata kunci" className="w-full rounded-xl border border-[var(--border)] bg-[var(--background)] py-3.5 pl-11 pr-4 font-mono text-sm text-[var(--foreground)] placeholder:text-[var(--muted-foreground)] transition focus:outline-none focus:ring-2 focus:ring-[var(--primary)] focus:ring-offset-2 focus:ring-offset-[var(--card)]" /></div>
            </label>
            <div className="flex flex-wrap items-center gap-2 text-[11px] text-[var(--muted-foreground)]">
              {queryKind === "post" && <label className="ml-auto inline-flex cursor-pointer items-center gap-2"><input type="checkbox" checked={fetchReplies} onChange={(event) => setFetchReplies(event.target.checked)} className="rounded border border-[var(--border)] accent-[var(--primary)] focus:outline-none focus:ring-2 focus:ring-[var(--primary)] focus:ring-offset-2 focus:ring-offset-[var(--card)]" />ambil balasan</label>}
            </div>
            <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
              <label className="block text-xs font-semibold text-[var(--foreground)]">Jumlah postingan
                <select value={limit} onChange={(event) => setLimit(event.target.value)} className="mt-2 block rounded-lg border border-[var(--border)] bg-[var(--background)] px-3 py-2.5 text-sm text-[var(--foreground)] transition focus:outline-none focus:ring-2 focus:ring-[var(--primary)] focus:ring-offset-2 focus:ring-offset-[var(--card)]"><option value="100">100 terbaru</option><option value="250">250 terbaru</option><option value="500">500 terbaru (maks.)</option></select>
              </label>
              <button type="submit" disabled={loading} className="inline-flex min-h-[48px] flex-1 cursor-pointer items-center justify-center gap-2 rounded-lg bg-[var(--primary)] px-5 py-3 text-sm font-bold text-white transition hover:opacity-90 focus:outline-none focus:ring-2 focus:ring-[var(--primary)] focus:ring-offset-2 focus:ring-offset-[var(--card)] disabled:cursor-not-allowed disabled:opacity-60">{loading ? <><Loader2 size={17} className="animate-spin" />Mengambil dan menganalisis...</> : <><Activity size={17} />Jalankan analisis</>}</button>
              <button type="button" onClick={handleClear} className="inline-flex min-h-[48px] cursor-pointer items-center justify-center gap-2 rounded-lg border border-[var(--border)] bg-[var(--card)] px-5 py-3 text-sm font-semibold text-[var(--foreground)] transition hover:bg-[var(--card-subtle)] focus:outline-none focus:ring-2 focus:ring-[var(--primary)] focus:ring-offset-2 focus:ring-offset-[var(--card)]"><RefreshCw size={15} />Bersihkan</button>
            </div>
            {errorMsg && <p role="alert" className="flex items-start gap-2 rounded-xl border border-red-500/25 bg-red-500/10 p-3 text-xs font-semibold leading-5 text-red-700 dark:text-red-300"><AlertTriangle size={15} className="mt-0.5 shrink-0" />{errorMsg}</p>}
          </form>
        </motion.div>

        <AnimatePresence>
          {result && <AnalysisPanel result={result} activeTab={activeResultTab} setActiveTab={setActiveResultTab} />}
        </AnimatePresence>
      </div>
    </section>
  );
}

function AnalysisPanel({ result, activeTab, setActiveTab }: { result: AnalysisResult; activeTab: ResultTab; setActiveTab: (tab: ResultTab) => void }) {
  const tabs: Array<{ id: ResultTab; label: string; icon: typeof Network }> = [
    { id: "overview", label: "Ringkasan", icon: BarChart3 },
    { id: "network", label: "Graf relasi", icon: Network },
    { id: "sentiment", label: "Sentimen", icon: HeartPulse },
    { id: "evidence", label: "Bukti teks", icon: Search },
    { id: "accounts", label: "Akun", icon: Users },
  ];
  const graph = result.graph;
  const hub = graph.hub as NetworkNode | null;
  return (
    <motion.div id="hasil-analisis" initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 30 }} className="mx-auto mt-12 max-w-6xl overflow-hidden rounded-[28px] border border-[var(--border)] bg-[var(--card)] shadow-[0_24px_80px_rgba(15,23,42,0.1)]">
      <div className="border-b border-[var(--border)] p-5 md:p-8">
        <div className="flex flex-col gap-5 lg:flex-row lg:items-center lg:justify-between">
          <div className="min-w-0"><div className="flex flex-wrap items-center gap-2 text-[10px] font-bold uppercase tracking-[0.16em] text-[var(--primary)]"><span>Hasil analisis</span><span className="text-[var(--muted-foreground)]">/</span><span>{result.source}</span></div><h2 className="mt-2 break-words text-xl font-extrabold text-[var(--foreground)] md:text-2xl">{result.query}</h2><p className="mt-2 flex flex-wrap items-center gap-2 text-xs text-[var(--muted-foreground)]"><Clock3 size={13} />{result.scannedPosts} postingan diproses</p></div>
          <div className="flex items-center gap-4 rounded-2xl border border-[var(--border)] bg-[var(--card-subtle)] px-4 py-3"><div className={`flex h-14 w-14 items-center justify-center rounded-full border-4 text-lg font-extrabold ${riskClass(result.riskLevel)}`}>{Math.round(result.score)}</div><div><div className="text-[10px] font-bold uppercase tracking-wider text-[var(--muted-foreground)]">Skor koordinasi</div><div className="mt-0.5 text-sm font-bold text-[var(--foreground)]">{riskLabel(result.riskLevel)}</div></div></div>
        </div>
        {result.warnings.length > 0 && <div className="mt-5 space-y-2 rounded-2xl border border-amber-500/25 bg-amber-500/10 p-4 text-xs leading-5 text-amber-900 dark:text-amber-200">{result.warnings.map((warning) => <p key={warning} className="flex gap-2"><AlertTriangle size={14} className="mt-0.5 shrink-0" />{warning}</p>)}</div>}
      </div>
      <div className="overflow-x-auto border-b border-[var(--border)] px-4 md:px-7"><div className="flex min-w-max gap-1">{tabs.map(({ id, label, icon: Icon }) => <button key={id} type="button" onClick={() => setActiveTab(id)} className={`inline-flex cursor-pointer items-center gap-2 border-b-2 px-3 py-3.5 text-xs font-bold transition focus:outline-none focus:ring-2 focus:ring-[var(--primary)] focus:ring-inset md:px-4 md:text-sm ${activeTab === id ? "border-[var(--primary)] text-[var(--primary)]" : "border-transparent text-[var(--muted-foreground)] hover:text-[var(--foreground)]"}`}><Icon size={15} />{label}</button>)}</div></div>
      <div className="p-5 md:p-8">
        {activeTab === "overview" && <div className="space-y-6">{result.accounts.length === 0 && result.scannedPosts === 0 && <Empty text="Analisis selesai, tetapi belum ada akun atau postingan yang dapat ditampilkan." />}<div className="grid grid-cols-2 gap-3 md:grid-cols-3 lg:grid-cols-6"><Metric label="Skor rata-rata" value={`${Math.round(result.score)}`} tone="primary" icon={Activity} /><Metric label="Akun" value={String(result.accounts.length)} icon={Users} /><Metric label="Post" value={String(result.scannedPosts)} tone="primary" icon={FileSearch} /><Metric label="Kemiripan" value={`${Math.round(result.duplicateRatio * 100)}%`} icon={Search} /><Metric label="Burst" value={`${Math.round(result.burstRatio * 100)}%`} tone="danger" icon={Clock3} /><Metric label="Edge graf" value={String(Number((graph.total_edges ?? graph.totalEdges) || 0))} tone="warning" icon={Network} /></div><div className="grid gap-6 lg:grid-cols-[1.35fr_0.65fr]"><div className="rounded-2xl border border-[var(--border)] bg-[var(--card-subtle)] p-5"><div className="mb-4 flex items-start justify-between gap-3"><div><h3 className="text-base font-bold text-[var(--foreground)]">Perbandingan Sinyal Analisis</h3><p className="mt-1 text-xs leading-5 text-[var(--muted-foreground)]">Perbandingan hanya ditampilkan jika respons menyediakan skor aktual untuk ketiga sinyal pada skala yang sama.</p></div></div><ModelComparison accounts={result.accounts} /></div><div className="rounded-2xl border border-[var(--border)] bg-[var(--card-subtle)] p-5"><div className="flex items-center gap-2 text-base font-bold text-[var(--foreground)]"><HeartPulse size={17} className="text-[var(--accent-danger)]" />Sentimen sampel</div><p className="mt-1 text-xs text-[var(--muted-foreground)]">Dominan: <strong className="text-[var(--foreground)]">{sentimentLabel(result.sentiment.dominant)}</strong></p><div className="mt-5"><SentimentBars sentiment={result.sentiment} /></div></div></div></div>}
        {activeTab === "network" && <div className="space-y-5"><div className="flex flex-col gap-2 md:flex-row md:items-end md:justify-between"><div><h3 className="text-lg font-extrabold text-[var(--foreground)]">Graf relasi pada sampel live</h3><p className="mt-1 max-w-2xl text-xs leading-5 text-[var(--muted-foreground)]">Layout mengikuti pola notebook: komponen terbesar, hub berdasarkan in-degree, arah edge, ukuran node berdasarkan degree, dan label untuk node penting.</p></div>{hub && <div className="rounded-xl border border-red-500/25 bg-red-500/10 px-3 py-2 text-xs text-red-700 dark:text-red-300">Hub: <strong>@{hub.username}</strong> · in-degree {hub.inDegree ?? 0}</div>}</div><HeroNetworkPreview nodes={result.networkNodes} edges={result.networkEdges} /><div className="grid grid-cols-2 gap-3 sm:grid-cols-4"><Metric label="Node total" value={String(Number(graph.graph_nodes ?? graph.total_nodes ?? graph.totalNodes ?? result.networkNodes.length))} /><Metric label="Edge total" value={String(Number(graph.graph_edges ?? graph.total_edges ?? graph.totalEdges ?? result.networkEdges.length))} /><Metric label="Komponen terbesar" value={String(Number(graph.largest_component_size ?? 0))} tone="primary" /><Metric label="Edge terlihat" value={String(result.networkEdges.length)} tone="warning" /></div></div>}
        {activeTab === "sentiment" && <div className="grid gap-6 lg:grid-cols-[0.8fr_1.2fr]"><div className="rounded-2xl border border-[var(--border)] bg-[var(--card-subtle)] p-5"><div className="flex items-center gap-2 text-lg font-bold text-[var(--foreground)]"><HeartPulse size={18} className="text-[var(--accent-danger)]" />Analisis sentimen</div><p className="mt-2 text-xs leading-5 text-[var(--muted-foreground)]">{result.sentiment.disclaimer}</p><div className="mt-6"><SentimentBars sentiment={result.sentiment} /></div><div className="mt-5 flex items-center justify-between rounded-xl border border-[var(--border)] bg-[var(--card)] p-3 text-xs"><span className="text-[var(--muted-foreground)]">Skor rata-rata</span><strong className="text-[var(--foreground)]">{Number(result.sentiment.average_score || 0).toFixed(2)}</strong></div><div className="mt-3 text-[10px] text-[var(--muted-foreground)]">Metode: {result.sentiment.method}</div></div><div className="space-y-3"><h3 className="text-base font-bold text-[var(--foreground)]">Contoh teks paling menonjol</h3>{result.sentiment.examples.length === 0 ? <Empty text="Belum ada sinyal sentimen yang cukup pada sampel." /> : result.sentiment.examples.map((example) => <div key={`${example.label}-${example.username}-${example.text}`} className="rounded-2xl border border-[var(--border)] bg-[var(--card-subtle)] p-4"><div className="flex items-center justify-between gap-3"><span className="rounded-full px-2.5 py-1 text-[10px] font-bold" style={{ backgroundColor: `${sentimentColor(example.label)}22`, color: sentimentColor(example.label) }}>{sentimentLabel(example.label)}</span><span className="text-[10px] text-[var(--muted-foreground)]">@{example.username} · {Number(example.score).toFixed(2)}</span></div><p className="mt-3 text-sm leading-6 text-[var(--foreground)]">{example.text}</p></div>)}</div></div>}
        {activeTab === "evidence" && <div className="grid gap-8 lg:grid-cols-[1fr_0.9fr]"><div><div className="mb-4 flex items-center gap-2"><Search size={17} className="text-[var(--primary)]" /><h3 className="text-lg font-extrabold text-[var(--foreground)]">Frasa berulang lintas akun</h3></div>{result.repeatedPhrases.length === 0 ? <Empty text="Belum ada pasangan frasa dengan kemiripan yang cukup." /> : <div className="space-y-3">{result.repeatedPhrases.map((phrase) => <div key={`${phrase.phrase}-${phrase.similarity}`} className="rounded-2xl border border-[var(--border)] bg-[var(--card-subtle)] p-4"><div className="flex items-start justify-between gap-4"><p className="min-w-0 text-sm font-semibold leading-6 text-[var(--foreground)]">&ldquo;{phrase.phrase}&rdquo;</p>{typeof phrase.similarity === "number" && Number.isFinite(phrase.similarity) && <span className="shrink-0 rounded-lg bg-amber-500/10 px-2.5 py-1 text-xs font-bold text-amber-700 dark:text-amber-300">{phrase.similarity}%</span>}</div><p className="mt-2 text-xs text-[var(--muted-foreground)]">Terlihat pada {phrase.count} postingan dari {phrase.accountCount ?? phrase.count} akun berbeda.</p></div>)}</div>}</div><div><div className="mb-4 flex items-center gap-2"><BarChart3 size={17} className="text-[var(--accent-warn)]" /><h3 className="text-lg font-extrabold text-[var(--foreground)]">Ringkasan bukti</h3></div><div className="space-y-3 rounded-2xl border border-[var(--border)] bg-[var(--card-subtle)] p-5 text-sm">{Object.entries(result.evidence).filter(([key]) => key !== "topHubs").map(([key, value]) => <div key={key} className="flex items-center justify-between gap-4 border-b border-[var(--border)] pb-3 last:border-0 last:pb-0"><span className="text-xs text-[var(--muted-foreground)]">{key.replace(/[A-Z]/g, (letter) => ` ${letter}`).replace(/^./, (letter) => letter.toUpperCase())}</span><strong className="text-[var(--foreground)]">{typeof value === "object" ? JSON.stringify(value) : String(value)}</strong></div>)}</div></div></div>}
        {activeTab === "accounts" && <div><div className="mb-5 flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between"><div><h3 className="text-lg font-extrabold text-[var(--foreground)]">Akun yang terdeteksi</h3><p className="mt-1 text-xs text-[var(--muted-foreground)]">Urutan berdasarkan skor fusion. Foto dan metadata berasal dari profil publik yang ikut terscrape.</p></div><span className="text-xs font-semibold text-[var(--muted-foreground)]">{result.accounts.length} akun</span></div>{result.accounts.length === 0 ? <Empty text="Tidak ada akun dari response backend." /> : <div className="grid gap-4 xl:grid-cols-2">{result.accounts.map((account) => <AccountCard key={account.id} account={account} />)}</div>}</div>}
      </div>
    </motion.div>
  );
}


function ModelComparison({ accounts }: { accounts: BuzzerAccount[] }) {
  const comparison = signalValues(accounts);
  if (!comparison) return <Empty text="Data perbandingan sinyal belum tersedia pada respons analisis ini" />;
  return <div className="space-y-4">{comparison.signals.map((signal) => { const value = clampPercentage(signal.values.reduce((sum, item) => sum + item, 0) / signal.values.length * comparison.scale); return <div key={signal.key}><div className="mb-1 flex justify-between text-xs"><span className="font-semibold text-[var(--foreground)]">{signal.label}</span><span className="tabular-nums text-[var(--muted-foreground)]">{value.toFixed(1)}%</span></div><div className="h-3 overflow-hidden rounded-full bg-[var(--border)]"><div className="h-full rounded-full" style={{ width: `${value}%`, backgroundColor: signal.color }} /></div></div>; })}</div>;
}

function AccountCard({ account }: { account: BuzzerAccount }) {
  const [open, setOpen] = useState(false);
  return <div className="rounded-2xl border border-[var(--border)] bg-[var(--card-subtle)] p-4 transition hover:-translate-y-0.5 hover:shadow-md"><div className="flex items-start gap-3"><ProfileAvatar account={account} size={48} /><div className="min-w-0 flex-1"><div className="flex flex-wrap items-center gap-2"><strong className="truncate text-sm text-[var(--foreground)]">{account.name || `@${account.username}`}</strong><span className={`rounded-full border px-2 py-0.5 text-[10px] font-bold ${riskClass(account.riskLevel)}`}>{account.prediction || riskLabel(account.riskLevel)}</span></div><span className="mt-0.5 block truncate text-xs text-[var(--muted-foreground)]">@{account.username}</span><p className="mt-2 line-clamp-2 text-xs leading-5 text-[var(--muted-foreground)]">{account.bio || account.explanation || "Metadata bio tidak tersedia."}</p></div><div className="shrink-0 text-right"><div className="tabular-score text-2xl text-[var(--foreground)]">{Math.round(account.buzzerScore)}</div><div className="text-[10px] uppercase tracking-wider text-[var(--muted-foreground)]">score</div></div></div><div className="mt-4 grid grid-cols-3 gap-2 text-center"><SmallStat label="Post" value={String(account.nPostsInDataset)} /><SmallStat label="Followers" value={formatFollowers(account.followers)} title={new Intl.NumberFormat("id-ID").format(Math.max(0, numeric(account.followers)))} /><SmallStat label="Sentimen" value={sentimentLabel(account.sentiment?.label || "neutral")} /></div><div className="mt-4 flex items-center justify-between gap-3"><span className="truncate text-xs text-[var(--muted-foreground)]">{account.explanation || "Belum ada evidence dominan"}</span><button type="button" onClick={() => setOpen((value) => !value)} className="inline-flex shrink-0 cursor-pointer items-center gap-1 rounded-lg border border-[var(--border)] bg-[var(--card)] px-2.5 py-1.5 text-[10px] font-bold text-[var(--foreground)]">Detail <ChevronDown size={13} className={open ? "rotate-180" : ""} /></button></div>{open && <div className="mt-4 space-y-3 border-t border-[var(--border)] pt-4"><div className="grid grid-cols-3 gap-2">{Object.entries(account.branchScores || {}).map(([key, value]) => <SmallStat key={key} label={key.replace("_", " ")} value={`${Math.round(Number(value) * 100)}%`} />)}</div><div className="text-xs leading-5 text-[var(--muted-foreground)]">Followers {account.followers.toLocaleString("id-ID")} · Following {account.following.toLocaleString("id-ID")} · Burst {Math.round(account.burstRatio * 100)}%</div>{account.tweets.slice(0, 5).map((tweet) => <div key={tweet.id} className="rounded-xl border border-[var(--border)] bg-[var(--card)] p-3"><div className="flex justify-between gap-2 text-[10px] text-[var(--muted-foreground)]"><span>{tweet.relationType} · {tweet.sentiment ? sentimentLabel(tweet.sentiment.label) : "sentimen -"}</span><span>{new Date(tweet.date).toLocaleString("id-ID")}</span></div><p className="mt-2 text-xs leading-5 text-[var(--foreground)]">{tweet.text}</p></div>)}</div>}</div>;
}

function SmallStat({ label, value, title }: { label: string; value: string; title?: string }) { return <div className="rounded-lg border border-[var(--border)] bg-[var(--card)] px-2 py-2"><div className="text-[9px] font-bold uppercase tracking-wider text-[var(--muted-foreground)]">{label}</div><div title={title} className="mt-0.5 truncate text-xs font-bold text-[var(--foreground)]">{value}</div></div>; }
function Empty({ text }: { text: string }) { return <div className="rounded-2xl border border-dashed border-[var(--border)] bg-[var(--card-subtle)] p-8 text-center text-sm text-[var(--muted-foreground)]">{text}</div>; }
