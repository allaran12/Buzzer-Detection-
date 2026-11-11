# Product Requirement Document (PRD)
# CoordinX: AI-Powered Coordinated Behavior & Buzzer Detection System

**Version:** 1.0  
**Status:** In Progress / Hackathon Ready  
**Target Platform:** X (formerly Twitter)  
**Target Domain:** Social Cyber, Coordinated Inauthentic Behavior (CIB), Cyber-troop/Buzzer Network Detection (Bahasa Indonesia context)

---

## 1. Executive Summary & Problem Statement

### 1.1 Latar Belakang
Di era digital, media sosial seperti platform X (Twitter) kerap dimanfaatkan oleh aktor tertentu melalui operasi terkoordinasi (cyber-troops / buzzer) untuk memanipulasi opini publik, menyebarkan narasi terarah (*astroturfing*), meningkatkan polarisasi sosial-politik, hingga melakukan kampanye disinformasi terstruktur.

Mendeteksi perilaku buzzer secara akurat merupakan tantangan multidimensi:
1. **Batas Samar antara Organik dan Terkoordinasi:** Aktivitas buzzer modern tidak lagi sekadar spam sederhana, melainkan melibatkan akun nyata atau semi-otomatis dengan gaya penulisan beragam.
2. **Keterbatasan Pendekatan Berdimensi Tunggal:** Analisis teks saja (NLP) atau analisis grafik saja tidak cukup untuk menangkap operasi yang memanfaatkan pola waktu serentak (*temporal burst*) dan relasi tersembunyi antar-akun.

### 1.2 Solusi: CoordinX
**CoordinX** hadir sebagai sistem kecerdasan buatan terpadu yang memadukan tiga pilar utama:
- **Analisis Semantik & Bahasa:** Menggunakan model NLP berbasis Transformer berbahasa Indonesia (*IndoBERTweet*) untuk memahami narasi teks, repetisi konten, dan parafrase buatan.
- **Analisis Pola Temporal:** Menganalisis sekuens waktu posting (*burstiness*, interval antar-postingan, dan ritme waktu) untuk mengidentifikasi postingan serentak yang tidak wajar.
- **Analisis Graf Interaksi (GNN):** Menggunakan graf relasi berarah (*GraphSAGE* & NetworkX) untuk membaca topologi jejaring (retweet, quote, reply, mention) dan mengidentifikasi sub-jaringan/klaster akun yang beroperasi secara bersama-sama.

---

## 2. Sasaran Pengguna & Persona (Target Audience)

1. **Jurnalis Investigasi & Pemeriksa Fakta (*Fact-Checkers*):** Membutuhkan bukti berbasis data (*evidence-based*) yang cepat untuk memverifikasi apakah suatu tren atau tagar di X merupakan percakapan organik masyarakat atau kampanye buatan (*astroturfing*).
2. **Peneliti Media Sosial & Keamanan Siber Sosial (*Social Cyber Researchers*):** Memerlukan metrik terstandarisasi, visualisasi jejaring, serta ekstraksi fitur untuk studi kuantitatif terkait jaringan manipulasi informasi.
3. **Masyarakat Umum / Netizen:** Ingin mengetahui apakah suatu isu viral di X digerakkan oleh akun-akun mencurigakan melalui antarmuka sederhana (Telegram Bot).

---

## 3. Fitur Utama Sistem (Core Features)

### 3.1 Pipeline Data (Ingestion & Preprocessing)
- **Scraper Fleksibel:** Integrasi scraping aman via `twscrape` berbasis session/cookie dengan dukungan pencarian URL tweet, hashtag, keyword, batas waktu (*since/days*), serta relasi balasan (*replies*).
- **Data Cleansing & Validation:** 
  - Memisahkan data korup/kosong ke `rejected_rows.csv`.
  - Deduping berdasarkan ID unik tweet (`post_id`) tanpa menghilangkan konteks relasi.
  - Mempertahankan entitas penting untuk analisis (URL, mention, hashtag, emoji).
- **Data Standardization:**
  - Standardisasi ID ke string presisi.
  - Standardisasi waktu posting ke format ISO-8601 UTC.
  - Parsing interaksi mention menjadi array terstruktur.
  - Tokenisasi khusus model NLP (`HTTPURL`, `@USER`, normalisasi emoji bahasa Indonesia).

### 3.2 Mesin Analisis & Pemodelan (AI Engine)
- **Modul 1: Heuristic & Rule-Based Scoring (Unsupervised Baseline)**
  - Kemiripan teks via TF-IDF n-gram & Cosine Similarity antar-akun berbeda.
  - Deteksi *burst* (frekuensi akun unik yang memposting dalam menit yang sama).
  - Rasio perilaku akun (status per hari, rasio following/follower, umur akun, kelengkapan bio/avatar).
- **Modul 2: Deep Learning NLP (IndoBERTweet)**
  - Ekstraksi embedding representasi semantik kalimat.
  - Pengelompokan teks bertema serupa yang diparafrase.
- **Modul 3: Temporal Sequence Modeling (LSTM / Inter-Arrival Times)**
  - Pembelajaran sekuens temporal aktivitas akun untuk membedakan ritme manusiawi vs otomasi terjadwal.
- **Modul 4: Graph Neural Network (GraphSAGE / PyG)**
  - Pembentukan graf interaksi antarpengguna: node = akun, edges = reply, quote, mention, retweet.
  - Pengenalan struktur koordinasi terpusat (*star topology*, *clique*, atau cincin koordinasi).
- **Modul 5: Multimodal Feature Fusion & Classifier**
  - Menggabungkan representasi NLP + Fitur Temporal + Node Embeddings Graf.
  - Menghasilkan probabilitas akun (*Account-Level Score*: 0 = Organik, 1 = Buzzer) dan identifikasi klaster kampanye (*Group-Level Detection*).

### 3.3 Antarmuka & Layanan Pengguna (Delivery Interfaces)
- **Backend API (FastAPI):** Menyediakan REST API performa tinggi untuk inferensi cepat:
  - `POST /api/v1/analyze/url`: Menerima URL tweet/percakapan dan mengembalikan hasil analisis cepat.
  - `POST /api/v1/analyze/batch`: Analisis batch dataset CSV.
  - `GET /api/v1/health`: Pengecekan status layanan dan scraper account pool.
- **Telegram Bot:**
  - User mengirimkan URL tweet atau tagar.
  - Bot membalas dengan *Executive Summary Card*: Skor koordinasi keseluruhan, persentase akun mencurigakan, top 3 akun paling mencurigakan, dan ringkasan narasi dominan.
- **Interactive Dashboard (Web UI / Streamlit):**
  - Visualisasi graf interaktif (node interaksi dan klaster akun buzzer).
  - Grafik tren volume percakapan dari waktu ke waktu (*timeline chart*).
  - Tabel rincian akun dengan filter metrik risiko.

---

## 4. Arsitektur Teknis & Spesifikasi Teknologi

| Komponen | Spesifikasi & Library |
|---|---|
| **Bahasa Pemrograman** | Python 3.10+ |
| **Data Ingestion** | `twscrape`, `asyncio`, `aiosqlite` |
| **Manipulasi Data** | `pandas`, `numpy`, `scipy` |
| **Text Processing & NLP** | Hugging Face `transformers`, `IndoBERTweet`, `emoji`, `scikit-learn` (TF-IDF) |
| **Pemodelan Sekuensial** | PyTorch (`torch.nn.LSTM`) |
| **Pemodelan Graf (GNN)** | `PyTorch Geometric (PyG)`, `NetworkX` |
| **Model Klasifikasi Baseline** | `RandomForestClassifier`, `StandardScaler`, `joblib` |
| **Backend API** | `FastAPI`, `uvicorn`, `pydantic` |
| **User Interface** | Telegram Bot (`python-telegram-bot` atau `aiogram`), Streamlit / Next.js |
| **Penyimpanan Metadata & Cache** | SQLite (`accounts.db`), Disk storage (`data/raw`, `data/interim`, `data/processed`) |

---

## 5. Struktur Data & Kontrak Skema

### 5.1 Skema Data Standar (`standardized_data.csv`)
Setiap data postingan yang masuk ke pipeline harus memenuhi format:
- `post_id` (str): ID unik tweet.
- `account_id` (str): ID unik pengguna pembuat tweet.
- `username` (str): Handle pengguna.
- `date` (datetime, UTC): Waktu penerbitan tweet (ISO-8601).
- `text` (str): Teks konten tweet asli.
- `text_bert` (str): Teks yang sudah dinormalisasi untuk IndoBERTweet.
- `relation_type` (str): Jenis relasi (`original`, `reply`, `retweet`, `quote`).
- `target_post_id` (str, nullable): ID tweet rujukan (jika reply/retweet/quote).
- `target_account_id` (str, nullable): ID akun target rujukan.
- `target_username` (str, nullable): Handle akun target rujukan.
- `mentioned_user_ids` (str/JSON list): Daftar ID akun yang dimention.
- `followers` (int): Jumlah pengikut.
- `following` (int): Jumlah akun yang diikuti.
- `statuses` (int): Total tweet akun sepanjang masa.
- `created` (datetime, UTC): Waktu akun dibuat.
- `bio` (str): Deskripsi profil akun.
- `avatar` (str): URL foto profil.
- `is_rt` (bool), `is_reply` (bool), `is_quote` (bool): Flag biner relasi.
- `isu` (str): Label topik / kampanye yang sedang dianalisis.

### 5.2 Skema Output Analisis Akun (`account_prediction.csv`)
- `account_id` / `username`
- `buzzer_probability` (float [0.0 - 1.0])
- `coordination_cluster_id` (int / str)
- `risk_level` (`Low`, `Medium`, `High`)
- `key_indicators` (list): Indikator kecurigaan utama (contoh: `"high_text_similarity"`, `"burst_activity"`, `"abnormal_follower_ratio"`).

---

## 6. Metrik Evaluasi & Target Performa

1. **Performa Deteksi (Evaluasi Model):**
   - **Precision (Target: > 80%):** Meminimalkan *false positive* agar akun organik tidak salah dilabeli sebagai buzzer.
   - **Recall (Target: > 75%):** Mampu menjaring mayoritas akun yang terlibat dalam operasi terkoordinasi.
   - **F1-Score (Target: > 78%):** Keseimbangan antara precision dan recall.
   - **ROC-AUC (Target: > 0.85):** Kemampuan separasi probabilitas kelas positif dan negatif.
2. **Latensi Sistem:**
   - Waktu inferensi per 1.000 tweet < 15 detik (menggunakan GPU) atau < 45 detik (menggunakan CPU).
   - Respon Telegram Bot untuk URL tunggal (termasuk scraping replies sampel) < 30 detik.

---

## 7. Roadmap Implementasi (Milestones)

### Fase 1: Fondasi Data & Baseline (Selesai Sebagian / In Progress)
- [x] Pembangunan scraper dengan Streamlit & `twscrape`.
- [x] Pipeline data cleaning dan standardisasi skema.
- [x] Baseline Unsupervised scoring (rule-based).
- [x] Tooling manual review dan anotasi data (`labeling_helper.py`).
- [x] Baseline Supervised (Random Forest).
- [ ] Konsolidasi direktori scraping & dataset mentah.

### Fase 2: Pipeline Fitur Lanjutan & Deep Learning (Target Utama)
- [ ] Ekstraksi embedding representasi teks dengan `IndoBERTweet`.
- [ ] Pembuatan modul pembentukan graf interaksi berarah (`NetworkX` & `PyG Dataset`).
- [ ] Implementasi arsitektur GNN (GraphSAGE) untuk node classification.
- [ ] Multimodal fusion layer (menggabungkan sinyal NLP, waktu, dan graf).

### Fase 3: Layanan & Integrasi Produk
- [ ] Pembangunan REST API dengan FastAPI.
- [ ] Pembangunan bot Telegram untuk query publik.
- [ ] Dashboard visualisasi web untuk eksplorasi graf dan timeline.

---

## 8. Prinsip Etika & Batasan Sistem (Disclaimer)

1. **Bukan Putusan Akhir (*Not Definitive Attribution*):** Prediksi sistem menunjukkan *probabilitas kecurigaan perilaku terkoordinasi*, bukan kepastian hukum bahwa pemilik akun adalah entitas jahat atau bot bayaran.
2. **Koordinasi Organik vs Inautentik:** Tidak semua koordinasi bersifat inautentik (misalnya: kampanye kemanusiaan, suporter sepak bola, atau aksi sosial warga). Hasil analisis wajib mempertimbangkan konteks narasi dan bukti pendukung.
3. **Privasi & Kebijakan Data:** Sistem hanya mengolah data yang tersedia secara publik pada platform X, tanpa menyimpan informasi rahasia atau identitas pribadi di luar akun publik.

