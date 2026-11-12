# CoordinX — Web Dashboard & Frontend PRD

## 1. Goal Statement
Build a fast, transparent, no-nonsense coordinated behavior & buzzer detection web platform for **CoordinX**, defined by clean white, a confident cobalt, and a tight geometric sans — built around an instant X post/hashtag inspection bar and an interactive Account Risk Inspector grid, with the 3-pillar AI scoring methodology (IndoBERTweet, LSTM, GraphSAGE), threshold tables, and ethical limitations stated openly on the page instead of hidden inside an academic PDF nobody opens.

## 2. Tech Stack
```
Next.js (App Router) + React + TypeScript + Tailwind CSS + Framer Motion (motion/react) + shadcn/ui + lucide-react
```
*Deploy target: **Vercel** (Frontend & Serverless API Bridge) + **FastAPI** (Python ML/GNN Inference Backend).*

## 3. Design System — Colors
```css
:root {
  --background: hsl(210, 22%, 98%);      /* #f9fbfc */
  --foreground: hsl(220, 30%, 14%);      /* #19202e */
  --primary: hsl(222, 84%, 48%);         /* #1450e0 cobalt */
  --primary-foreground: hsl(0, 0%, 100%);
  --muted-foreground: hsl(220, 8%, 46%);
  --border: hsl(212, 18%, 89%);
  --card: hsl(210, 26%, 95%);
  --accent-go: hsl(150, 58%, 40%);       /* organic / safe */
  --accent-warn: hsl(32, 90%, 52%);      /* suspicious / medium */
  --accent-danger: hsl(350, 84%, 54%);   /* high-risk buzzer */
}
```

## 4. Typography
```html
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet" />
```
- **H1:** Plus Jakarta Sans 800, `clamp(36px, 4.6vw, 64px)`, `letter-spacing: -0.03em`
- **H2:** Plus Jakarta Sans 700, `30–42px`
- **H3 / account handles & model names:** Plus Jakarta Sans 700, `18–21px`
- **Body:** Inter 300–400, `16px`, `line-height: 1.7`
- **Eyebrows:** Inter 600, uppercase, `letter-spacing: 0.16em`, `11px`, cobalt (`#1450e0`)
- **Buzzer Scores / Post Rates / Follower Ratios:** Plus Jakarta Sans 800, `tabular-nums`

## 5. Visual Effects

**Effect 1 — Inspection Bar with Live Scope & Latency Estimate.** An X URL / hashtag input bar with sample depth, time window, and engine mode selectors that computes the estimated number of posts scanned and inference time beneath as the parameters change, before anyone runs a full scan.

```tsx
const [depth, setDepth] = useState<number>(200);
const [mode, setMode] = useState<"fast" | "deep">("deep");
const estSeconds = mode === "deep" ? Math.max(4, Math.round(depth / 35)) : Math.max(2, Math.round(depth / 120));

{depth > 0 && (
  <motion.p
    key={`${depth}-${mode}`}
    initial={{ opacity: 0, y: 6 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ duration: 0.25 }}
    className="mt-4 text-sm text-[var(--muted-foreground)]"
  >
    Up to <span className="font-bold text-[var(--foreground)] tabular-nums">{depth} posts</span> · est.{" "}
    <span className="font-bold text-[var(--foreground)] tabular-nums">~{estSeconds}s</span> via{" "}
    {mode === "deep" ? "IndoBERTweet + LSTM + GraphSAGE" : "TF-IDF Heuristic"}, full breakdown included
  </motion.p>
)}
```

**Effect 2 — Account Risk Card with Metric Reveal.** Account inspector cards (and clickable rows) where hovering lifts the card, scales the avatar/network cluster badge slightly, and fades in a four-item diagnostic row of `Followers Ratio`, `Post Rate`, `Text Similarity`, and `Burst Sync` beneath the Buzzer Score. Clicking opens the **Account Deep-Dive Drawer** with 4-pillar score decomposition and sample tweets.

## 6. Component Breakdown

1. **Navbar** — `70px`, sticky, white, `1px` bottom border. Wordmark `COORDINX` left, links centre (`Inspector`, `Methodology`, `Thresholds`, `Datasets`, `API & Bot`), Engine Status badge & `Analyze URL` cobalt button right.
2. **Hero** — `78vh`, split. Text and URL/Hashtag inspection bar left, clean interactive Network Topology & Risk Score preview right. Eyebrow, H1, subline, inspection bar, four trust points. *Visual: crisp modular SVG cluster graph on a bright neutral surface (`#f9fbfc`), clear node states (cobalt/emerald/amber/rose).*
3. **Trust Strip** — zero login required, 3-pillar explainable AI, raw evidence preserved, methodology stated in four words.
4. **Account Risk Inspector (The Suspects Grid & Table)** — the main section. Category filter chips (`All`, `High Risk (Buzzer)`, `Suspicious`, `Organic`, `Cluster Leaders`) + Campaign Issue selector (`All Issues`, `#PrayForKalimantan`, `Pilpres wowo2`, `RoySuryo`, `JokowiWowo`) + search & CSV export, followed by a grid/table of analyzed accounts (Effect 2), each with Risk Tier, Buzzer Score (`0–100`), 4-item diagnostic metric row, status badge, and click-to-inspect drawer (showing bio, 4-pillar breakdown, and actual sample tweets).
5. **What is Measured vs What is Not (Honesty Block)** — six signals that are actually measured by CoordinX, each with a tick, and three claims that CoordinX deliberately does NOT make, each with a cross. This transparency block is the differentiator in a domain full of opaque black-box "bot scores".
6. **Risk Tiers & Threshold Policy** — a plain table of the three risk classification tiers (`Organic`, `Suspicious`, `High-Risk Buzzer`) with score thresholds, key triggers, confidence level, and recommended action.
7. **NLP, Temporal & Graph Policy** — two short paragraphs stating the exact analytical rules (preserving emojis/hashtags/mentions for IndoBERTweet, burstiness intervals, and GraphSAGE reply/quote topology) and known exceptions (organic viral activism, breaking news spikes).
8. **How It Works** — four steps from submitting an X URL/hashtag to inspecting account-level and cluster-level evidence, including what preprocessing safeguards are applied.
9. **Monitored Datasets & Endpoints** — three active Indonesian campaign datasets (`#PrayForKalimantan`, `Pilpres wowo2`, `RoySuryo`) with post volume, unique account count, date window, and CSV/JSON export note.
10. **API & Telegram Bot Integration** — endpoint specs and usage tiers (`/api/v1/analyze/url`, `/api/v1/analyze/batch`, and `@CoordinXBot` on Telegram), aimed at investigative journalists, fact-checkers, and social cyber researchers.
11. **FAQ** — accordion, six questions on organic vs coordinated behavior, Indonesian slang & emoji handling, why hashtags/mentions aren't stripped, data privacy (public X posts only), FastAPI model connection, and false-positive appeals.
12. **Footer** — deep navy (`#19202e`), four columns, project status (Social Cyber Hackathon), model stack credits, ethical disclaimer, and GitHub link (`allaran12/Buzzer-Detection-`).

## 7. Animations
- **Hero:** text fades up `0.6s`; inspection bar scales `0.98` to `1` with a soft shadow, `0.5s`
- **Live scope estimate:** re-mounts and fades up on depth/mode change, `0.25s`
- **Filter chips:** background transition `0.2s`; account grid/table re-flows with Framer Motion `layout`, `0.32s`
- **Account cards:** lift `4px`, avatar/badge scales `1.03`, 4-item diagnostic row fades in over `0.25s` on hover
- **Measured vs Not-Claimed lists:** tick and cross icons pop scale `0.7` to `1`, staggered `0.05s`
- **Step numbers:** pop staggered `0.1s`
- Everything is crisp and responsive — this is an analytical investigation tool, not a decorative showcase.

## 8. Responsive
- **Mobile (`<768px`):** hamburger menu; hero graph preview drops below the inspection bar; H1 clamps to `36px`; inspection bar stacks into four full-width fields with a sticky `Analyze` button; account grid 1-col; threshold table becomes stacked cards; filter chips horizontally scrollable.
- **Tablet:** account grid 2-col, hero stays split, threshold table retained.
- **Desktop:** account grid 4-col (or structured inspector table + graph split), max width `1240px`, `px-16`, `py-20`.

## 9. Full Copy

**Brand:** COORDINX · AI Coordinated Behavior Detection · IndoBERTweet · LSTM · GraphSAGE

**Navbar:** Inspector · Methodology · Thresholds · Datasets · API & Bot · `FastAPI: Ready` · [Button] Analyze URL

**Hero**
- Eyebrow: `INDONESIAN SOCIAL CYBER · NLP · TEMPORAL · GRAPH NEURAL NETWORK`
- H1: `See the coordination behind the trend.`
- Subline: `Open-methodology buzzer & coordinated behavior analysis for X (Twitter). Semantic similarity, posting burst synchrony, and interaction graphs laid out transparently before you draw a conclusion.`
- Inspection bar: `X Post URL or #Hashtag` · `Sample depth (100–2000)` · `Window (7–30d)` · `Engine Mode` · [Button] `Analyze`
- Trust points: `Zero black-box scores` · `Public X data only` · `IndoBERTweet + GraphSAGE` · `Full evidence export`

**Account Risk Inspector** — Eyebrow `THE SUSPECTS` — H2 `Account risk, exposed with receipts`
Filters: `All` · `High Risk (Buzzer)` · `Suspicious` · `Organic` · `Amplifiers`
Issues: `All Issues` · `#PrayForKalimantan` · `Pilpres wowo2` · `RoySuryo` · `JokowiWowo`

Sample Accounts (backed by dataset schemas):
1. **@WempiF90099 (Cluster Alpha)** — Score `92/100` — `20.0x flw ratio · 18.5/hr · 88% sim · 94% burst` — *High Risk (Buzzer)*
2. **@cyber_indojaya99 (Cluster Beta)** — Score `89/100` — `37.0x flw ratio · 22.0/hr · 92% sim · 91% burst` — *High Risk (Buzzer)*
3. **@buzzer_senter07 (Cluster Gamma)** — Score `84/100` — `17.3x flw ratio · 14.8/hr · 79% sim · 85% burst` — *High Risk (Buzzer)*
4. **@Uniliswara0 (Amplifier)** — Score `68/100` — `0.12x flw ratio · 8.4/hr · 54% sim · 62% burst` — *Suspicious*
5. **@notnamern (Cluster Beta)** — Score `54/100` — `1.14x flw ratio · 5.2/hr · 65% sim · 48% burst` — *Suspicious*
6. **@ccaramelh2h (Activist)** — Score `34/100` — `0.24x flw ratio · 2.0/hr · 22% sim · 35% burst` — *Organic*
7. **@BuchroniK (Commentator)** — Score `28/100` — `0.74x flw ratio · 0.8/hr · 18% sim · 15% burst` — *Organic*
8. **@naraeraa (Citizen)** — Score `22/100` — `0.14x flw ratio · 1.1/hr · 12% sim · 20% burst` — *Organic*

**What is Measured vs Not Claimed** — H2 `What the risk score actually measures`
Measured: `Cross-account semantic & copypasta similarity (IndoBERTweet / TF-IDF)` · `Per-minute posting bursts & inter-arrival synchrony (LSTM)` · `Reply, quote & mention network centrality (GraphSAGE)` · `Account age & extreme following-to-follower anomalies` · `Hashtag stuffing & automated posting cadence` · `Preserved raw evidence (sample tweets, timestamps & targets)`
Not Claimed: `Definitive legal proof of paid cyber-troop employment` · `Automated guilt without human context review` · `Private personal data or non-public account metadata`

**Risk Tiers & Thresholds**
| Risk Tier | Score Range | Primary Triggers | Action |
|---|---|---|---|
| Organic | `0 – 39` | Natural cadence, unique phrasing, balanced network graph | No flag; baseline conversation |
| Suspicious | `40 – 69` | High hashtag overlap, amplifier behavior, or moderate burst timing | Manual review via sample tweets |
| High-Risk Buzzer | `70 – 100` | Synchronized <60s bursts + >75% text similarity + isolated cluster edges | Flagged in cluster graph & CSV export |

Note: `CoordinX preserves original hashtags, URLs, mentions, and Indonesian emojis rather than stripping them during preprocessing, because coordinated campaigns frequently hide inside identical hashtag blocks and emoji patterns.`

**NLP, Temporal & Graph Policy** — `Multi-pillar fusion. A single identical tweet does not make an account a buzzer, and high activity during a breaking disaster is normal. CoordinX requires converging signals across semantic similarity (IndoBERTweet), temporal synchrony (LSTM burst intervals), and structural reply/quote clustering (GraphSAGE) before elevating a risk tier.`
`All data pipelines enforce UTC ISO-8601 timestamp standardization and string-precision post/account IDs so cross-branch comparisons and graph edges never silently drop due to integer overflow.`

**How It Works**
1. **Submit** — Paste an X post URL, `#hashtag`, or search query into the inspection bar (or pick a preprocessed dataset).
2. **Preprocess** — `cleaning.py` & `standardization.py` validate required IDs, isolate duplicates, standardize UTC timestamps, and format tokens (`@USER`, `HTTPURL`, Indonesian demojization).
3. **Score** — The 3-pillar engine evaluates semantic repetition, burst synchrony, and reply/quote network graphs to compute an explainable `0–100` score.
4. **Inspect** — Click any account to inspect its 4-pillar score breakdown, cluster graph neighbors, and verbatim tweet timestamps, or export the table to CSV.

**Monitored Datasets**
- **#PrayForKalimantan** — `4,120 raw posts · Standardized & cleaned` · Focus: Environmental disaster & regional protest narratives
- **Pilpres wowo2** — `6,529 cleaned posts · Interim & feature-ready` · Focus: Political polarization & coordinated reply clusters
- **RoySuryo & Political Issues** — `3,677 raw posts · Labeled baseline batch` · Focus: Influencer target amplification & quote-tweet rings
Note: `Raw and standardized CSV datasets reside in data/raw/ and data/processed/, ready for immediate batch inspection or FastAPI model serving.`

**API & Telegram Bot** — `FastAPI REST endpoints (/api/v1/analyze/url & /api/v1/analyze/batch) · Vercel Serverless Proxy (/api/accounts & /api/analyze) · Telegram Bot (@CoordinXBot). Designed for investigative journalists, fact-checkers, and research teams who need fast, reproducible evidence cards in under 30 seconds.`

**FAQ**
1. **Does a high score prove an account is a paid buzzer?** — No. CoordinX measures statistical coordination and bot-like anomalies. High scores require human context review to distinguish malicious astroturfing from passionate organic activism.
2. **How does CoordinX handle Indonesian slang and emojis?** — Text preprocessing uses `clean_bert` tailored for IndoBERTweet: it normalizes repeated characters, replaces URLs/mentions with tokens (`HTTPURL`, `@USER`), and converts emojis into Indonesian text descriptors rather than deleting them.
3. **Why keep hashtags, URLs, and mentions?** — Coordinated networks often copy-paste identical hashtag stacks or coordinate replies toward the exact same target account. Stripping them destroys the strongest structural signal.
4. **What data does CoordinX collect?** — Only publicly accessible X posts and public profile counters (followers, following, statuses, bio, creation date) collected via `twscrape`. No private DMs or personal non-public data are stored.
5. **Can this frontend connect to our custom Python model?** — Yes. Set `FASTAPI_BACKEND_URL` in Vercel environment variables and `/api/analyze` automatically proxies requests to your FastAPI IndoBERTweet/GraphSAGE server, falling back cleanly to demo mode when offline.
6. **Can I export results for further research?** — Yes. Every filtered view in the Account Risk Inspector exports directly to `.csv` with full scores, ratios, and cluster IDs.

**Footer** — COORDINX · `See the coordination behind the trend.` · Social Cyber Hackathon Project · Model Stack: IndoBERTweet · LSTM · GraphSAGE · Ethical Disclaimer & Methodology · © 2026

## 10. Key Dependencies
```json
{
  "next": "16.4.6",
  "react": "19.3.0",
  "react-dom": "19.3.0",
  "motion": "^12.0.0",
  "lucide-react": "^0.460.0",
  "@radix-ui/react-accordion": "^1.2.0",
  "clsx": "^2.1.0",
  "tailwind-merge": "^2.5.0"
}
```

## final