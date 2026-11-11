# COORDINX — REPOSITORY AUDIT REPORT
**Audit Date:** 2026-11-09  
**Reference Document:** `PRD.md` (Version 1.0)  
**Auditor:** Codex / Lead AI Engineer  
**Status:** Active pipeline standardized through Phase 5

---

## 1. Current Project Structure

Setelah pembersihan file usang (`.DS_Store`, fragment duplikat) dan standarisasi penamaan per-kategori:

```text
Buzzer-Detection-/
├── PRD.md                                 # Single source of truth spesifikasi sistem
├── README.md                              # Dokumentasi umum awal proyek
├── LICENSE                                # Apache 2.0
├── models/                                # Model artifacts terlatih
│   └── phase5_baseline_rf.pkl             # Baseline RF Phase 5 (Batch 2+3)
├── data/
│   ├── raw/                               # Raw scraped CSV (tidak boleh diubah)
│   │   ├── prayforkalimantan.csv          # Isu Karhutla (Batch 1, 350K)
│   │   ├── wowo2.csv                      # Isu Prabowo/Teddy (Batch 2, 1.2M)
│   │   ├── RoySuryo.csv                   # Isu Roy Suryo/Ijazah (Batch 3, 780K)
│   │   └── jokowi.csv, riaricis.csv, wowo.csv # Dataset sekunder
│   ├── interim/                           # Hasil Data Cleaning per-isu
│   │   ├── RoySuryo/                      # 1,081 baris bersih, 18 duplikat disaring
│   │   └── wowo2_cleaned/                 # 1,514 baris bersih
│   ├── processed/                         # Hasil Data Standardization per-isu
│   │   ├── prayforkalimantan/
│   │   ├── wowo2/
│   │   └── RoySuryo/                      # UTC timestamps, Int64, mention JSON
│   ├── features/                          # Ekstraksi fitur tabular & network
│   │   ├── batch2_posts_with_features.csv
│   │   ├── batch2_account_features.csv
│   │   ├── batch2_account_features_with_scores.csv
│   │   ├── batch3_posts_with_features.csv
│   │   ├── batch3_account_features.csv
│   │   └── batch3_account_features_with_scores.csv
│   ├── labels/                            # Ground truth anotasi manusia
│   │   ├── batch2_top30_for_review.csv
│   │   ├── batch2_random20_for_review.csv
│   │   ├── batch2_labeled_combined.csv    # 50 akun (23 buzzer, 27 organik)
│   │   ├── batch3_top30_for_review.csv
│   │   ├── batch3_random20_for_review.csv
│   │   └── batch3_labeled_combined.csv    # 50 akun (29 buzzer, 21 organik)
│   └── predictions/                       # Direktori output inferensi (reserved)
├── notebooks/                             # Jupyter notebooks eksperimen
│   ├── clean analysis.ipynb               # Feature engineering & NetworkX graph
│   ├── 04a_unsupervised_baseline.ipynb    # Scoring z-score & sampling review
│   └── 04b_supervised_baseline.ipynb      # Supervised training RF baseline
├── src/
│   ├── preprocessing/
│   │   ├── cleaning.py                    # Dedup post_id, filter teks kosong
│   │   ├── standardization.py             # Casting tipe data & standarisasi UTC
│   │   ├── labeling_helper.py             # Interactive CLI labeling (Batch 2 & 3)
│   │   └── processing.py                  # Skrip lama (hardcoded all_tweets.csv)
│   └── screpping/                         # Koleksi scraper & merger SQLite
│       ├── screpping.py                   # Playwright/Twitter scraper
│       ├── marge.py                       # Skrip gabung raw CSV
│       └── accounts.db                    # Database SQLite session akun
├── output/                                # Visualisasi hasil analisis
│   ├── phase5/                            # Metrics, confusion matrices, dan OOF predictions
│   └── batch3/                            # Visualisasi historis RoySuryo
├── archive/                               # Arsip eksperimen lama & backup batch (tidak dipakai pipeline aktif)
└── reports/                               # Laporan audit & dokumentasi teknis
    └── REPOSITORY_AUDIT.md
```

---

## 2. Existing Implementation

Pipeline yang saat ini aktif dan berjalan:

1. **Scraping (`src/screpping/`):** Menggunakan Playwright untuk mengambil tweet publik berdasarkan query isu.
2. **Data Cleaning (`src/preprocessing/cleaning.py`):**
   - Menghapus duplikasi berdasarkan `post_id`.
   - Memfilter baris tanpa teks atau identitas `post_id`/`account_id`.
   - Mengisolasi baris rejected dan duplicate ke CSV terpisah.
3. **Data Standardization (`src/preprocessing/standardization.py`):**
   - Mengonversi tanggal ke format UTC ISO-8601 (`YYYY-MM-DDTHH:MM:SSZ`).
   - Menyimpan `post_id`, `account_id`, `conversation_id` sebagai string.
   - Mengubah kolom numerik (`followers`, `following`, `statuses`) ke `Int64`.
   - Memetakan array mention ke JSON valid string.
4. **Feature Engineering (`notebooks/clean analysis.ipynb`):**
   - Post-level: `n_tags`, `body_len`, `body_clean`, `has_url`, `relation_type`.
   - Account-level: `n_posts`, `avg_tags`, `avg_body_len`, `post_rate`, `follower_ratio`.
   - Network graph: Dibangun dengan NetworkX (`in_degree`, `out_degree`, `pagerank`).
5. **Unsupervised Scoring (`notebooks/04a_unsupervised_baseline.ipynb`):**
   - Agregasi StandardScaler dari 5 indikator perilaku untuk menghasilkan `buzzer_score` (0.0 – 1.0).
   - Memilih 30 akun teratas (*suspicious*) + 20 akun acak (*baseline*).
6. **Anotasi Manual (`src/preprocessing/labeling_helper.py`):**
   - CLI interaktif menampilkan profil akun, metrik, dan sample teks postingan.
   - Menghasilkan file gabungan 50 akun per-batch.
7. **Supervised Training (`notebooks/04b_supervised_baseline.ipynb`):**
   - Group CV, temporal holdout, dan cross-issue evaluation.
   - Random Forest/Logistic baseline, confusion matrix, PR-AUC, dan report Phase 5.

---

## 3. Working Components

Komponen yang terbukti stabil dan berfungsi tanpa error:

- `src/preprocessing/cleaning.py`: Berhasil membersihkan dataset wowo2 dan RoySuryo tanpa kehilangan presisi ID.
- `src/preprocessing/standardization.py`: Berjalan deterministik, menghasilkan laporan parsing yang akurat.
- `src/preprocessing/labeling_helper.py`: Mendukung argumen `batch2` dan `batch3`, menampilkan sample postingan secara akurat, dan menyimpan progres secara bertahap.
- `notebooks/04b_supervised_baseline.ipynb`: Berhasil mengevaluasi 100 akun berlabel dari 2 isu dengan group CV, temporal holdout, dan cross-issue evaluation.

---

## 4. Broken or Incomplete Components

Komponen yang belum sempurna atau perlu perbaikan:

1. **`src/preprocessing/processing.py`:** Membaca file `data/all_tweets.csv` yang tidak ada dalam repository (legacy dead code).
2. **`src/screpping/`:** Penamaan folder mengandung typo (`screpping` vs `scraping`), dan `marge.py` mengandung typo (`marge` vs `merge`).
3. **IndoBERTweet Branch:** Belum ada modul ekstraksi embedding teks 768-dimensi (hanya ada fungsi pembersih regex dasar di `processing.py`).
4. **Temporal LSTM Branch:** Belum ada representasi urutan sekuens waktu per akun.
5. **Graph Neural Network (GraphSAGE):** Baru berupa metrik topologi NetworkX sederhana (`in_degree`, `out_degree`, `pagerank`), belum ada PyTorch Geometric embedding.
6. **Feature Fusion:** Belum ada arsitektur penggabung multi-modal.

---

## 5. Data Quality Concerns

1. **Skews Observasi Singkat (Low Observation Count):**
   - Pada dataset `RoySuryo.csv`, 796 akun menghasilkan 1,081 postingan.
   - Mayoritas akun (>70%) hanya memiliki **1 postingan**. Akibatnya, `active_hours` bernilai 0 dan `post_rate` dipatok pada nilai *fallback* (10.0 post/jam). Hal ini mendistorsi analisis temporal.
2. **Jaringan Terputus (Dangling Edges):**
   - Dari 738 edge interaksi reply/quote, banyak target akun (`target_account_id`) yang tweet aslinya berada di luar dataset scraping.
3. **Format ID Preservasi:**
   - Masih ada beberapa bagian di notebook lama yang memuat ID tanpa `dtype="string"`, berisiko terkonversi ke scientific notation (float64).

---

## 6. Potential Data Leakage

1. **Data Leakage pada Normalisasi:**
   - Pada beberapa sel notebook `04a` dan `04b`, `StandardScaler` dipasang (*fitted*) pada seluruh dataset sebelum split data training/testing dilakukan.
2. **Selection Bias pada Evaluasi:**
   - 50 akun yang dianotasi manual dipilih berdasarkan 30 skor kecurigaan tertinggi + 20 acak. Jika dievaluasi dengan random split biasa, model cenderung menguji distribusi yang tidak representatif terhadap populasi akun sesungguhnya.
3. **Ketiadaan Group/Account Split:**
   - Jika satu akun muncul di beberapa postingan atau isu, akun yang sama berpotensi bocor ke data train dan test secara bersamaan.

---

## 7. Modeling Concerns

1. **Pergeseran Domain Lintas Isu (*Domain Shift*):**
   - Karakteristik buzzer pada Isu Prabowo/Teddy (Batch 2) berbeda secara signifikan dengan Isu Roy Suryo (Batch 3):
     - Batch 2: Buzzer dominan menggunakan kalimat pendek dan repetitif.
     - Batch 3: Buzzer justru membuat kutipan argumen panjang (panjang karakter rata-rata 198 karakter vs organik 144 karakter).
   - Akibatnya, model yang dilatih murni pada Batch 2 gagal total saat diuji pada Batch 3 (Akurasi anjlok ke 44%, Buzzer Recall hanya 17.2%).
2. **Ukuran Sampel Uji Terlalu Kecil pada Notebook Awal:**
   - Evaluasi di `04b` pada 10 sampel uji menghasilkan ROC-AUC 0.438. Metrik pada sampel sekecil ini tidak memiliki signifikansi statistik.
3. **Retrained Combined Model Sebagai Mitigasi:**
   - Evaluasi Phase 5 disimpan di `reports/BASELINE_EVALUATION_REPORT.md`; hasil group CV dan cross-issue dipisahkan agar tidak menyamarkan domain shift.

---

## 8. Missing Tests

1. Belum ada folder `tests/` di root proyek.
2. Belum ada unit test otomatis untuk memvalidasi:
   - Preservasi string ID akun dan post.
   - Konsistensi format timestamp ISO-8601 UTC.
   - Pengecekan deduplikasi `post_id`.
   - Integritas relasi edge reply dan quote.

---

## 9. Recommended Next Steps

Mengikuti arahan roadmap PRD:

1. **Phase 1: Dataset Quality & Pipeline Modularization:**
   - Buat unit test sederhana berbasis `assert` (`tests/test_data_quality.py`) untuk memvalidasi keutuhan string ID dan timestamp.
   - Rapikan `src/preprocessing/` menjadi library Python modular yang dapat diimpor tanpa hardcoded path.
2. **Phase 2: Standardisasi Label Ground Truth (Sesuai PRD Section 10):**
   - Transisi skema label dari biner murni (`1/0`) menjadi 3 kategori: `Positive`, `Negative`, `Unknown`.
   - Tambahkan kolom pencatatan bukti (*evidence*) pada file anotasi.
3. **Phase 3: Cross-Issue Validation Benchmark (PRD Section 11.3):**
   - Bangun skrip validasi resmi: Train pada Isu A, Evaluasi pada Isu B untuk mengukur kemampuan generalisasi model sebelum menambahkan arsitektur kompleks.

---

## 10. Mapping Kondisi Proyek vs PRD

| PRD Requirement | Deskripsi | Status Repository Saat Ini |
|---|---|---|
| **FR-01** | Import dataset CSV | ✅ Berjalan (`cleaning.py`, `standardization.py`) |
| **FR-02** | Column mapping dinamis | ⚠️ Parsial (mapping kolom masih terikat schema tetap) |
| **FR-03** | Data quality validation | ✅ Berjalan (laporan cleaning & standardization tercatat) |
| **FR-04** | ID preservation (string murni) | ✅ Berjalan (string casting diterapkan di pipeline) |
| **FR-05** | Post deduplication | ✅ Berjalan (deduplikasi berdasarkan `post_id`) |
| **FR-06** | Text preprocessing | ⚠️ Parsial (pembersihan URL/mention ada, tokenisasi NLP belum) |
| **FR-07** | Text similarity analysis | ❌ Belum diimplementasikan |
| **FR-08** | Temporal feature extraction | ⚠️ Dasar (`active_hours`, `post_rate`), urutan waktu belum |
| **FR-09** | Interaction graph construction | ✅ Berjalan via NetworkX (`in_degree`, `out_degree`, `pagerank`) |
| **FR-10** | Account-level feature extraction | ✅ Berjalan (6 fitur inti terekstraksi) |
| **FR-11** | Model training pipeline | ✅ Berjalan (`notebooks/04b_supervised_baseline.ipynb`) |
| **FR-12** | Model evaluation & visualization | ✅ Berjalan (Confusion Matrix, PR/F1, ROC-AUC otomatis) |
| **FR-13** | Coordination scoring | ⚠️ Parsial (unsupervised buzzer score 0-1) |
| **FR-14** | Evidence explanation | ❌ Belum diimplementasikan |
| **FR-15** | Human review workflow | ✅ Berjalan via `labeling_helper.py` |
| **FR-16** | Cross-issue evaluation | ⚠️ Sedang dikembangkan (uji silang wowo2 vs RoySuryo) |
| **FR-17** | Export analysis report | ⚠️ Parsial (laporan teks dan gambar tersimpan di `output/`) |
| **FR-18** | Dashboard visualization | ❌ Belum diimplementasikan (Future) |

---
**Kesimpulan Audit:**  
Fondasi data dan baseline tabular Random Forest sudah berada di jalur yang benar (Akurasi gabungan 85%). Kelemahan utama proyek saat ini adalah belum adanya modul deep learning (NLP, LSTM, GraphSAGE), ketiadaan unit test otomatis, dan rentannya model terhadap pergeseran gaya postingan antar-isu.
