# Landing Page Analytics Refresh Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Perbarui landing page NEXANTARA agar hasil analisis aktual tampil lebih jelas sebagai visual analitik profesional tanpa mengubah backend, API, database, autentikasi, atau pipeline model.

**Architecture:** Pertahankan `Hero.tsx` sebagai orkestrator request dan normalisasi data. Perbaiki komponen hasil yang sudah ada dengan visual CSS/SVG ringan, state kosong/transparan, dan pemetaan followers dari `BuzzerAccount.followers`; revisi komponen presentasi lain hanya untuk hierarki visual dan copy yang akurat.

**Tech Stack:** Next.js 16, React 19, TypeScript, Tailwind CSS 4, lucide-react, motion.

**Spec:** `docs/superpowers/specs/2026-11-13-landing-page-analytics-refresh-design.md`

## Global Constraints

- Jangan mengubah API endpoint, backend, database, autentikasi, atau pipeline model.
- Jangan menambah dependency chart; gunakan CSS/SVG dan library yang sudah tersedia.
- Jangan menggunakan data dummy atau angka statis sebagai data produksi.
- Followers harus berasal dari `BuzzerAccount.followers`, bukan degree fields.
- Jangan menyebut model terlatih bila respons aktual tidak menyediakan branch score yang valid.
- Grafik harus aman untuk nilai kosong, null, negatif, dan non-finite.
- Pertahankan input analisis, tab hasil, network preview, dan fungsi lama.

## Review Focus

- Respons analisis tanpa akun/postingan harus menampilkan empty state yang jelas, bukan ringkasan seolah-olah ada data — diuji pada Task 1.
- `branchScores` parsial atau tidak tersedia harus tidak menghasilkan nilai 0 yang menyesatkan — diuji pada Task 1.
- Persentase sentimen null/negatif/non-finite harus menghasilkan lebar bar valid 0–100% — diuji pada Task 1.
- Pemetaan label akun harus menampilkan followers dan tidak lagi menampilkan Degree — diuji pada Task 1.
- Loading/error state dan layout mobile harus tetap berfungsi setelah perubahan visual — diverifikasi pada Task 2.

---

### Task 1: Perbaiki visualisasi dan integritas data pada panel hasil

**Files:**
- Modify: `web/src/components/Hero.tsx:286-301, 419-461`
- Test: Tidak tersedia test runner frontend; verifikasi melalui TypeScript compile, lint, dan build.

**Interfaces:**
- Consumes: `AnalysisResult.sentiment`, `BuzzerAccount.branchScores`, `BuzzerAccount.followers`, existing account/network data.
- Produces: visual Sentimen Sampel dengan bar dan tooltip native; model comparison hanya saat branch score aktual tersedia; AccountCard dengan label Followers; empty states untuk hasil kosong dan model unavailable.

- [ ] **Step 1: Tambahkan helper data presentation yang aman**
  Definisikan helper lokal untuk clamp angka ke 0–100, format followers dengan `Intl.NumberFormat("id-ID", { notation: "compact", maximumFractionDigits: 1 })`, dan mengambil hanya branch score yang finite dari akun. Jangan mengubah field API atau nama internal.

- [ ] **Step 2: Perbaiki `SentimentBars` menjadi visual distribusi aktual**
  Render kategori Positif, Negatif, dan Netral sebagai fokus utama, pertahankan Campuran bila count/percentage aktual tersedia. Gunakan persentase yang di-clamp, jumlah sampel, warna status konsisten, `title` pada bar untuk tooltip native, dan empty state ketika total sampel 0.

- [ ] **Step 3: Ganti blok “Sinyal utama sampel” dengan model comparison yang transparan**
  Gunakan judul “Perbandingan Hasil Analisis Model” dan subjudul sesuai spec. Render grouped horizontal bars/cards untuk IndoBERT, LSTM, dan GraphSAGE hanya jika ketiga branch memiliki data finite pada skala yang sama. Jika tidak, tampilkan state “Data perbandingan model belum tersedia pada respons analisis ini” dan jangan mengubah missing value menjadi 0. Hindari klaim “3-pilar fusion” ketika branch score tidak ada.

- [ ] **Step 4: Ganti Degree menjadi Followers di `AccountCard`**
  Ubah hanya label tampilan menjadi Followers dan sumber nilainya menjadi `account.followers`. Tampilkan format compact dengan tooltip angka lengkap; pertahankan Post dan Sentimen serta detail akun lainnya.

- [ ] **Step 5: Tambahkan empty state untuk hasil analisis kosong**
  Pada panel overview, bedakan `accounts.length === 0 && scannedPosts === 0` dari hasil normal, berikan pesan informatif, dan tetap pertahankan warning backend jika tersedia.

- [ ] **Step 6: Jalankan pemeriksaan statis setelah perubahan komponen**
  Run: `npm run lint` dan `npx tsc --noEmit` dari `web/`.
  Expected: lint dan TypeScript selesai tanpa error.

### Task 2: Rapikan arah visual landing page dan komponen pendukung

**Files:**
- Modify: `web/src/components/Hero.tsx:377-409`
- Modify: `web/src/components/Navbar.tsx`
- Modify: `web/src/components/AboutUs.tsx`
- Modify: `web/src/components/HowItWorks.tsx`
- Modify: `web/src/app/globals.css`

**Interfaces:**
- Consumes: Existing section IDs, theme tokens, motion behavior, and current analysis form.
- Produces: landing page with restrained borders/backgrounds, consistent spacing, responsive controls, accessible focus states, and accurate algorithm copy.

- [ ] **Step 1: Remove decorative excess from hero surface**
  Replace the strongest glow/shadow treatment with restrained border/card surfaces while preserving section hierarchy and existing form behavior.

- [ ] **Step 2: Improve responsive hierarchy and accessibility**
  Ensure form labels, buttons, tabs, and mobile navigation retain visible focus states, readable contrast, and no horizontal overflow except intentional result tabs.

- [ ] **Step 3: Correct algorithm copy without changing runtime behavior**
  Avoid claiming verified production implementations where the project report identifies proxies; describe the analysis pillars accurately and keep existing user-facing meaning.

- [ ] **Step 4: Normalize section/card spacing and typography tokens**
  Apply consistent container widths, section padding, border radii, and muted text treatment through existing Tailwind classes/CSS variables; do not introduce a new design system or dependency.

- [ ] **Step 5: Run full frontend verification**
  Run: `npm run lint`, `npx tsc --noEmit`, and `npm run build` from `web/`.
  Expected: all commands pass; build completes with the existing webpack configuration.

### Task 3: Verify backend/API integrity and regression surface

**Files:**
- No backend files should change.
- Verify: `web/src/app/api/analyze/route.ts`, `services/inference_api/main.py`, and existing Python tests remain untouched.

**Interfaces:**
- Consumes: Existing API contract and test suite.
- Produces: Evidence that frontend-only changes preserve backend integration.

- [ ] **Step 1: Inspect diff for forbidden backend/config changes**
  Run: `git diff --stat` and `git diff -- web/src/app/api services/inference_api`.
  Expected: only intended frontend files and the design/plan documents are changed; no API/backend diff.

- [ ] **Step 2: Run existing backend regression tests**
  Run: `python -m unittest discover -s tests -v` from repository root.
  Expected: existing tests pass; any pre-existing failures are recorded explicitly.

- [ ] **Step 3: Review final behavior against acceptance criteria**
  Confirm actual sentiment data drives the graph, model comparison is unavailable rather than fabricated when branch data is absent, account cards use followers, and the original analyze flow remains intact.

---

## Self-review

- Spec coverage: visual hierarchy, sentiment graph, transparent model comparison, followers mapping, responsive states, no backend changes, and verification are covered by Tasks 1–3.
- Type consistency: all values remain on existing `AnalysisResult`, `BuzzerAccount`, and `branchScores` fields; no new API contract is introduced.
- Review focus: each listed failure mode is owned by Task 1 or Task 2 and verified by static/build checks plus manual contract review.
- Proportion: plan limits edits to the existing landing-page implementation and avoids architecture or dependency changes.
