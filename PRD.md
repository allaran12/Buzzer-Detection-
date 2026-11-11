# PRODUCT REQUIREMENTS DOCUMENT (PRD)
# CoordinX — Social Media Coordination Detection System

**Document Version:** 1.0  
**Project Status:** Research & Development / Prototype  
**Platform Target:** X (formerly Twitter)  
**Primary Language:** Indonesian  
**Development Environment:** Python, Google Colab, GitHub  
**AI Coding Agent:** OpenAI Codex

---

# 1. Project Overview

## 1.1 Project Name

**CoordinX — Social Media Coordination Detection System**

## 1.2 Project Description

CoordinX adalah sistem analisis media sosial berbasis kecerdasan buatan yang dirancang untuk mendeteksi indikasi perilaku koordinasi tidak autentik (*coordinated inauthentic behavior*) pada platform X.

Sistem menganalisis pola aktivitas akun dan hubungan antar-postingan melalui beberapa pendekatan:

- Natural Language Processing (NLP): menganalisis isi dan kemiripan teks.
- Temporal Analysis: menganalisis pola waktu dan keserentakan aktivitas.
- Graph Analysis: menganalisis hubungan interaksi antar-akun.
- Machine Learning / Deep Learning: menggabungkan berbagai indikator untuk menghasilkan penilaian.

CoordinX tidak bertujuan memberikan vonis mutlak bahwa suatu akun adalah buzzer. Sistem memberikan indikasi, skor, pola pendukung, dan tingkat ketidakpastian yang dapat ditinjau oleh manusia.

## 1.3 Project Vision

Membangun sistem yang dapat digunakan untuk menganalisis berbagai isu di media sosial Indonesia tanpa bergantung pada satu topik, peristiwa, kelompok, atau dataset tertentu.

Contoh isu yang dapat dianalisis:

- Isu sosial.
- Isu politik.
- Kebijakan publik.
- Isu ekonomi.
- Isu lingkungan.
- Isu masyarakat dan peristiwa viral.

**Prinsip utama:** CoordinX harus bersifat general-purpose. Model tidak boleh hanya belajar mengenali kata, hashtag, nama tokoh, atau topik tertentu sebagai indikator buzzer.

---

# 2. Problem Statement

## 2.1 Permasalahan Utama

Penyebaran informasi di media sosial dapat melibatkan aktivitas banyak akun yang menunjukkan pola koordinasi.

Beberapa pola yang mungkin muncul:

1. Banyak akun mempublikasikan teks yang sangat mirip.
2. Banyak akun menggunakan slogan atau hashtag yang sama.
3. Banyak akun mempublikasikan konten dalam rentang waktu yang berdekatan.
4. Akun-akun tertentu memiliki pola interaksi yang saling terhubung.
5. Terdapat kelompok akun yang berulang kali berinteraksi atau memperkuat konten tertentu.
6. Beberapa akun menunjukkan pola aktivitas yang tidak biasa dibandingkan pola normal.

Namun, pola tersebut tidak otomatis membuktikan bahwa aktivitas dilakukan secara terkoordinasi atau tidak autentik.

Sebagai contoh:
- Banyak pengguna menggunakan hashtag yang sama karena sedang membicarakan peristiwa viral.
- Banyak pengguna membagikan slogan yang sama karena memiliki pendapat serupa.
- Banyak akun mengunggah konten pada waktu yang sama karena mengikuti berita yang sedang berkembang.

Karena itu, deteksi tidak boleh hanya mengandalkan satu indikator.

## 2.2 Masalah pada Pendekatan Deteksi Sederhana

Pendekatan berbasis frekuensi posting, hashtag, atau kemiripan teks saja memiliki risiko:

- False positive: pengguna organik dianggap sebagai akun terkoordinasi.
- False negative: pola koordinasi yang lebih kompleks tidak terdeteksi.
- Bias topik: model menganggap topik atau kata tertentu sebagai ciri buzzer.
- Label noise: data pelatihan mengandung label yang belum tentu benar.
- Data leakage: akun yang sama masuk ke data training dan testing.
- Overfitting: model hanya mengenali pola dari dataset yang digunakan saat pelatihan.

## 2.3 Permasalahan Dataset Saat Ini

Dataset yang dikumpulkan masih bersifat eksperimental dan perlu melalui proses audit.

Masalah yang harus diperhatikan:

1. Jumlah data masih terbatas.
2. Label buzzer dan organik belum sepenuhnya tervalidasi.
3. Identitas akun harus menggunakan ID akun yang stabil, bukan hanya username.
4. Relasi reply dan quote perlu divalidasi berdasarkan ID postingan.
5. Beberapa postingan target mungkin berada di luar dataset hasil scraping.
6. Data scraping berpotensi mengandung duplikasi.
7. Teks hasil scraping perlu diperiksa apakah mengandung metadata atau artefak scraper.
8. Riwayat postingan setiap akun tidak selalu cukup untuk menghasilkan fitur temporal yang kuat.
9. Kemiripan teks tidak selalu berarti koordinasi.
10. Data dari satu isu tidak cukup untuk membuktikan kemampuan generalisasi model.

## 2.4 Hasil Evaluasi Awal

Salah satu batch eksperimen sebelumnya menghasilkan:

| Metric | Hasil |
|---|---:|
| Accuracy | 0.60 |
| Buzzer Precision | 0.67 |
| Buzzer Recall | 0.67 |
| Buzzer F1-score | 0.67 |
| ROC-AUC | 0.438 |

Hasil tersebut menggunakan jumlah sampel pengujian yang sangat kecil, yaitu 10 sampel.

Hasil ini belum dapat dijadikan bukti bahwa model sudah mampu mendeteksi buzzer secara akurat.

Permasalahan yang perlu diteliti:
- Apakah label ground truth sudah benar?
- Apakah data training cukup representatif?
- Apakah fitur yang digunakan benar-benar menunjukkan koordinasi?
- Apakah terdapat data leakage?
- Apakah probabilitas dan urutan kelas pada perhitungan ROC-AUC sudah benar?
- Apakah arsitektur model terlalu kompleks dibandingkan ukuran dataset?

Codex harus membantu mengaudit masalah tersebut sebelum mengembangkan model lebih jauh.

---

# 3. Product Objectives

## 3.1 Primary Objectives

CoordinX harus mampu:

1. Menerima dataset postingan X.
2. Melakukan validasi dan preprocessing data.
3. Mengidentifikasi pola kemiripan konten antar-akun.
4. Mengidentifikasi pola aktivitas berdasarkan waktu.
5. Membentuk graph hubungan antar-akun.
6. Mengekstrak fitur pada tingkat postingan, akun, dan jaringan.
7. Menggabungkan indikator NLP, temporal, dan graph.
8. Menghasilkan skor indikasi koordinasi.
9. Menampilkan bukti yang mendukung hasil analisis.
10. Menyediakan mekanisme human review untuk memeriksa hasil.

## 3.2 Secondary Objectives

- Mendukung analisis berbagai isu.
- Memungkinkan dataset baru ditambahkan tanpa mengubah keseluruhan pipeline.
- Mendukung identifikasi kelompok akun yang memiliki pola koordinasi.
- Menyimpan riwayat analisis.
- Menyediakan laporan hasil analisis yang dapat dipahami pengguna non-teknis.

## 3.3 Non-Goals

Untuk tahap awal, CoordinX tidak bertujuan:

- Membuktikan identitas asli pemilik akun.
- Menentukan afiliasi politik seseorang.
- Menyimpulkan bahwa suatu akun dibayar oleh pihak tertentu.
- Memberikan vonis otomatis bahwa akun tertentu adalah buzzer.
- Melakukan pemantauan seluruh pengguna X secara real-time.
- Mengambil tindakan otomatis terhadap akun.
- Menyimpulkan niat seseorang hanya dari aktivitas postingan.

---

# 4. Target Users

## 4.1 Primary Users

- Peneliti media sosial.
- Mahasiswa dan akademisi.
- Tim analisis informasi digital.
- Pengguna yang ingin mempelajari pola koordinasi di media sosial.

## 4.2 User Needs

Pengguna membutuhkan sistem yang dapat menjawab pertanyaan:

1. Apakah terdapat indikasi koordinasi pada kumpulan postingan ini?
2. Akun mana yang menunjukkan pola aktivitas serupa?
3. Apakah terdapat kemiripan teks yang signifikan?
4. Apakah beberapa akun mempublikasikan konten dalam waktu yang berdekatan?
5. Bagaimana hubungan interaksi antar-akun?
6. Apa bukti yang mendukung hasil deteksi?
7. Seberapa yakin sistem terhadap hasil tersebut?
8. Apakah hasil ini perlu ditinjau manusia?

---

# 5. Scope and System Workflow

## 5.1 High-Level Workflow

Data Collection  
→ Data Validation  
→ Data Cleaning  
→ Feature Engineering  
→ NLP Analysis  
→ Temporal Analysis  
→ Graph Construction  
→ Model Inference  
→ Feature Fusion  
→ Coordination Scoring  
→ Human Review  
→ Report Generation

## 5.2 Input

Input utama berupa CSV hasil pengumpulan postingan X.

Sistem harus mendukung variasi nama kolom melalui konfigurasi pemetaan kolom.

Contoh data:

| Field | Description |
|---|---|
| post_id | ID unik postingan |
| account_id | ID unik akun |
| username | Username akun |
| text | Isi postingan asli |
| date | Waktu postingan |
| relation_type | original, reply, quote |
| target_post_id | ID postingan yang dibalas/dikutip |
| target_account_id | ID akun target |
| target_username | Username target |
| conversation_id | ID percakapan |
| followers | Jumlah followers |
| following | Jumlah following |
| statuses | Jumlah postingan akun |
| isu | Isu yang sedang dianalisis |
| query | Query pengumpulan data |

Field tambahan dapat digunakan jika tersedia.

## 5.3 Output

Output minimal:

- Daftar postingan yang dianalisis.
- Daftar akun yang dianalisis.
- Skor indikasi koordinasi.
- Fitur yang berkontribusi pada skor.
- Kelompok akun yang memiliki hubungan.
- Pola waktu aktivitas.
- Kemiripan konten.
- Visualisasi jaringan.
- Tingkat keyakinan.
- Status human review.
- Ringkasan laporan.

---

# 6. Data Architecture

## 6.1 General Data Principle

CoordinX harus memisahkan identitas akun dari isu yang sedang dianalisis.

Satu akun dapat muncul pada banyak isu. Identitas akun tidak boleh berubah hanya karena isu atau dataset berbeda.

Gunakan:

- `account_id`: identitas global akun.
- `post_id`: identitas global postingan.
- `issue_id`: metadata isu.
- `dataset_id`: identitas batch atau sumber dataset.

Jangan menjadikan username sebagai primary key karena username dapat berubah.

## 6.2 Recommended Data Entities

### Accounts

- account_id
- username
- followers
- following
- statuses
- bio
- first_seen
- last_seen

### Posts

- post_id
- account_id
- text_original
- text_clean
- created_at
- relation_type
- target_post_id
- target_account_id
- conversation_id
- dataset_id

### Issues

- issue_id
- issue_name
- issue_description
- start_date
- end_date

### Post Issue Mapping

- post_id
- issue_id

Satu postingan dapat memiliki lebih dari satu konteks isu apabila memang relevan.

### Interactions

- source_account_id
- target_account_id
- source_post_id
- target_post_id
- interaction_type
- timestamp

### Annotations

- entity_id
- entity_type
- label
- evidence
- annotator_id
- annotation_timestamp
- review_status

### Model Predictions

- entity_id
- entity_type
- model_version
- coordination_score
- prediction
- confidence
- evidence_summary
- prediction_timestamp

---

# 7. Data Quality and Preprocessing Requirements

## 7.1 Data Validation

Sistem harus memeriksa:

- Kolom wajib tersedia.
- post_id tidak kosong.
- account_id tidak kosong.
- Timestamp dapat diparsing.
- Format ID valid.
- Relasi postingan konsisten.
- Jumlah duplikasi.
- Teks kosong.
- Teks tidak valid.
- Nilai numerik yang tidak masuk akal.
- Potensi artefak hasil scraping.

## 7.2 ID Preservation

ID X dapat memiliki digit yang sangat panjang.

Wajib:
- Membaca ID sebagai string.
- Tidak mengonversi ID menjadi float.
- Tidak menggunakan scientific notation.
- Tidak mengubah ID melalui operasi numerik.
- Mempertahankan nilai asli dari sumber.

Apabila ID sudah kehilangan presisi saat proses pengumpulan, sistem harus menandainya sebagai data bermasalah. Jangan mencoba menebak nilai aslinya.

## 7.3 Deduplication

Deduplikasi utama menggunakan `post_id`.

Jangan menghapus postingan berbeda hanya karena teksnya sama atau mirip.

Jika satu post_id memiliki metadata yang saling bertentangan:
- Tandai sebagai conflict.
- Simpan informasi sumber.
- Jangan menghapus konflik tanpa laporan.
- Gunakan aturan pemilihan yang transparan.

## 7.4 Text Preprocessing

Simpan tiga bentuk teks:

1. `text_original`: teks asli.
2. `text_clean`: teks yang telah dibersihkan untuk analisis.
3. `text_model_input`: teks yang disiapkan untuk model.

Jangan menghilangkan hashtag, mention, emoji, atau URL secara otomatis sebelum mengevaluasi kontribusinya.

Preprocessing harus modular sehingga setiap eksperimen dapat dibandingkan.

## 7.5 Timestamp

- Standarkan timestamp ke UTC.
- Simpan timestamp asli jika tersedia.
- Konversi zona waktu hanya untuk kebutuhan tampilan.
- Jangan mencampurkan timestamp lokal dan UTC saat menghitung selisih waktu.

---

# 8. Feature Engineering

Fitur harus dibangun pada tiga level.

## 8.1 Post-Level Features

Contoh:

- Text embedding.
- Text similarity.
- Hashtag similarity.
- Mention similarity.
- URL similarity.
- Text length.
- Number of hashtags.
- Number of mentions.
- Posting time.
- Relation type.

## 8.2 Account-Level Features

Contoh:

- Total posts.
- Posts per time window.
- Average posting interval.
- Posting frequency.
- Burst activity.
- Average text similarity with other accounts.
- Number of unique interaction targets.
- In-degree.
- Out-degree.
- Degree centrality.
- Betweenness centrality.
- Clustering coefficient.

Fitur harus memperhitungkan jumlah observasi setiap akun. Akun dengan satu atau dua postingan tidak boleh diperlakukan sama dengan akun yang memiliki riwayat panjang.

## 8.3 Network-Level Features

Contoh:

- Connected components.
- Community detection.
- Degree distribution.
- Density.
- Reciprocity.
- Clustering coefficient.
- Centrality.
- Repeated interaction patterns.
- Cross-account synchronization.

Semua fitur graph harus memiliki definisi arah edge yang konsisten.

Contoh:
`source_account_id → target_account_id`

---

# 9. Proposed AI Architecture

## 9.1 Overall Architecture

Arsitektur yang direncanakan:

**IndoBERTweet + Temporal LSTM + Graph Neural Network**

Namun, implementasi harus dilakukan secara bertahap dan dibandingkan dengan baseline sederhana.

Jangan langsung menggabungkan seluruh model sebelum masing-masing komponen terbukti memberikan kontribusi.

## 9.2 NLP Branch — IndoBERTweet

Tujuan:
Menganalisis karakteristik bahasa dan kemiripan konten postingan.

Input:
- text_model_input

Output:
- Text embedding.
- Semantic representation.
- Text similarity features.

Catatan:
IndoBERTweet tidak boleh digunakan untuk menyimpulkan bahwa suatu opini politik atau hashtag tertentu merupakan bukti buzzer.

## 9.3 Temporal Branch — LSTM

Tujuan:
Menganalisis urutan aktivitas akun berdasarkan waktu.

Input:
- Urutan fitur aktivitas akun.
- Interval antar-postingan.
- Frekuensi postingan.
- Burst activity.
- Temporal representation.

Output:
- Temporal embedding.
- Indikasi pola aktivitas yang tidak biasa.

Catatan:
LSTM membutuhkan urutan data yang cukup. Jika data terlalu sedikit, gunakan baseline statistik terlebih dahulu.

## 9.4 Graph Branch — GNN / GraphSAGE

Tujuan:
Menganalisis hubungan antar-akun dan pola jaringan.

Input:
- Node: account.
- Edge: reply, quote, atau relasi lain yang tervalidasi.
- Node features.
- Edge features.

Output:
- Node embedding.
- Graph representation.
- Network relationship features.

Graph harus mempertahankan identitas akun global dan dapat dibangun ulang untuk setiap dataset atau isu.

## 9.5 Feature Fusion

Representasi dari ketiga cabang digabungkan:

`NLP Embedding + Temporal Embedding + Graph Embedding`

Hasilnya diteruskan ke classifier.

Output classifier bukan vonis buzzer, melainkan estimasi indikasi koordinasi.

## 9.6 Baseline Models

Sebelum model gabungan, implementasikan:

1. Logistic Regression.
2. Random Forest.
3. XGBoost atau model boosting lain jika tersedia.
4. IndoBERTweet-only.
5. Temporal-only.
6. Graph-only.
7. Fusion model.

Tujuannya mengetahui apakah arsitektur kompleks benar-benar memberikan peningkatan.

---

# 10. Labeling and Ground Truth

## 10.1 Labeling Principle

Label tidak boleh ditentukan hanya berdasarkan:

- Hashtag yang sama.
- Kesamaan opini.
- Frekuensi postingan.
- Kemiripan teks.
- Jumlah followers.
- Interaksi dengan akun tertentu.
- Skor model sebelumnya.

Semua hal tersebut merupakan indikator atau fitur, bukan ground truth.

## 10.2 Recommended Labels

Gunakan tiga kategori:

### Positive

Terdapat bukti kuat dan dapat diverifikasi mengenai pola koordinasi tidak autentik.

### Negative

Terdapat bukti yang cukup untuk mengklasifikasikan aktivitas yang diamati sebagai perilaku organik atau independen.

### Unknown

Bukti belum cukup untuk membuat kesimpulan.

Unknown tidak boleh dipaksa menjadi Positive atau Negative hanya untuk memenuhi kebutuhan training.

## 10.3 Annotation Requirements

Setiap label harus menyimpan:

- Entity ID.
- Entity type.
- Label.
- Evidence.
- Reason.
- Annotator.
- Timestamp.
- Review status.

Jika memungkinkan, gunakan lebih dari satu annotator dan hitung inter-annotator agreement, misalnya Cohen's Kappa.

## 10.4 Label Granularity

Bedakan:

- Post-level label.
- Account-level label.
- Group/network-level label.

Jangan menganggap satu postingan yang mirip dengan postingan lain otomatis membuktikan bahwa seluruh akun terkoordinasi.

---

# 11. Model Evaluation

## 11.1 Metrics

Gunakan:

- Accuracy.
- Precision.
- Recall.
- F1-score.
- Confusion matrix.
- ROC-AUC jika sesuai.
- PR-AUC untuk kondisi kelas tidak seimbang.
- Calibration metrics jika skor probabilitas ditampilkan.

Jangan hanya menggunakan accuracy.

## 11.2 Data Splitting

Hindari random split biasa apabila dapat menyebabkan akun yang sama muncul di training dan testing.

Prioritaskan:

- Group split berdasarkan account_id untuk menguji generalisasi ke akun baru.
- Temporal split untuk menguji generalisasi pada periode berikutnya.
- Issue-based evaluation untuk menguji generalisasi lintas isu.

Laporkan metode split yang digunakan.

## 11.3 Cross-Issue Generalization

Salah satu target utama CoordinX adalah kemampuan analisis lintas isu.

Contoh eksperimen:

- Train pada beberapa isu.
- Test pada isu yang tidak digunakan selama training.
- Bandingkan hasil.
- Analisis apakah model hanya menghafal kata atau hashtag tertentu.

Jangan menyatakan model general-purpose sebelum eksperimen tersebut berhasil.

## 11.4 Error Analysis

Setiap eksperimen harus mengidentifikasi:

- False positives.
- False negatives.
- Data yang salah label.
- Akun dengan data terlalu sedikit.
- Kesalahan graph construction.
- Kesalahan preprocessing.
- Potensi data leakage.

---

# 12. System Functional Requirements

| ID | Requirement | Priority |
|---|---|---|
| FR-01 | Import dataset CSV | Must |
| FR-02 | Column mapping | Must |
| FR-03 | Data quality validation | Must |
| FR-04 | ID preservation | Must |
| FR-05 | Post deduplication | Must |
| FR-06 | Text preprocessing | Must |
| FR-07 | Text similarity analysis | Must |
| FR-08 | Temporal feature extraction | Must |
| FR-09 | Interaction graph construction | Must |
| FR-10 | Account-level feature extraction | Must |
| FR-11 | Model training pipeline | Must |
| FR-12 | Model evaluation | Must |
| FR-13 | Coordination scoring | Must |
| FR-14 | Evidence explanation | Must |
| FR-15 | Human review | Must |
| FR-16 | Cross-issue evaluation | Should |
| FR-17 | Export analysis report | Should |
| FR-18 | Dashboard visualization | Future |

---

# 13. Non-Functional Requirements

## 13.1 Reproducibility

- Set random seeds.
- Save configuration.
- Record dataset version.
- Record model version.
- Save evaluation results.
- Log preprocessing parameters.

## 13.2 Modularity

Setiap komponen harus terpisah:

- Data ingestion.
- Data validation.
- Preprocessing.
- NLP.
- Temporal analysis.
- Graph analysis.
- Model training.
- Evaluation.
- Inference.
- Reporting.

## 13.3 Maintainability

- Gunakan Python.
- Gunakan fungsi yang memiliki tanggung jawab jelas.
- Hindari kode duplikat.
- Gunakan konfigurasi terpisah.
- Tambahkan dokumentasi.
- Tambahkan unit tests untuk fungsi penting.

## 13.4 Data Safety

- Jangan menimpa raw dataset.
- Simpan hasil setiap tahap secara terpisah.
- Jangan menghapus data tanpa laporan.
- Jangan mengubah label manual tanpa persetujuan.
- Jangan mengekspos informasi pribadi yang tidak diperlukan.

---

# 14. Dataset Status and Current Known Issues

## 14.1 RoySuryo Dataset

Dataset terbaru yang diberikan:

`RoySuryo.csv`

Hasil pemeriksaan awal:

| Item | Result |
|---|---:|
| Raw rows | 1,099 |
| Unique post IDs | 1,081 |
| Duplicate rows by post ID | 18 |
| Clean rows | 1,081 |
| Reply | 621 |
| Quote | 117 |
| Original | 361 |
| Reply/quote edges | 738 |

File hasil audit:

- `coordinx_roysuryo_raw_preserved.csv`
- `coordinx_roysuryo_cleaned.csv`
- `coordinx_roysuryo_quality_report.csv`
- `coordinx_roysuryo_edges.csv`

Catatan:
- ID dibaca sebagai string.
- Deduplikasi berdasarkan post_id.
- Teks yang sama tidak otomatis dihapus.
- Target postingan yang tidak ada dalam dataset tetap disimpan.
- Edge dibentuk dari relasi reply dan quote yang tersedia.
- Dataset ini belum dapat dianggap sebagai ground truth buzzer.

## 14.2 Earlier Experimental Dataset

Eksperimen sebelumnya juga menggunakan dataset dengan ukuran lebih kecil, termasuk dataset 416 postingan.

Hasil dan fitur dari eksperimen terdahulu harus tetap disimpan sebagai riwayat eksperimen, bukan digabungkan begitu saja dengan dataset RoySuryo.

Setiap dataset/batch harus memiliki identitas dan provenance masing-masing.

## 14.3 Important Instruction

Codex harus memeriksa file dan struktur repository aktual sebelum menganggap nama file, jumlah kolom, atau lokasi file masih sama.

Angka di atas merupakan catatan audit saat PRD dibuat, bukan nilai yang harus di-hardcode ke dalam program.

---

# 15. Development Roadmap

## Phase 0 — Repository Audit

Tujuan:
Memahami kondisi project saat ini.

Tasks:
- Inspect seluruh struktur repository.
- Inspect notebook, script, dataset, dan konfigurasi.
- Identifikasi pipeline yang sudah tersedia.
- Identifikasi kode duplikat.
- Identifikasi bagian yang belum berjalan.
- Buat dokumentasi kondisi awal.
- Jangan mengubah kode sebelum audit selesai.

Deliverable:
- Repository audit report.
- Current architecture diagram.
- List of bugs and technical debt.

## Phase 1 — Dataset Quality and Standardization

Tasks:
- Buat data ingestion module.
- Buat column mapping.
- Validasi ID.
- Validasi timestamp.
- Audit duplicate posts.
- Audit relation metadata.
- Audit missing values.
- Audit scraping artifacts.
- Standardisasi schema.
- Simpan raw dan cleaned dataset secara terpisah.

Deliverable:
- Standardized dataset.
- Quality report.
- Data validation tests.

## Phase 2 — Exploratory Data Analysis

Tasks:
- Distribusi postingan.
- Distribusi akun.
- Distribusi jenis interaksi.
- Distribusi waktu.
- Analisis aktivitas akun.
- Analisis kemiripan teks.
- Analisis hashtag.
- Analisis interaksi.
- Visualisasi awal.

Deliverable:
- EDA report.
- Feature exploration report.

## Phase 3 — Feature Engineering

Tasks:
- Text similarity features.
- Temporal features.
- Account-level features.
- Graph structural features.
- Network community features.
- Feature validation.

Deliverable:
- Feature dataset.
- Feature dictionary.
- Feature validation report.

## Phase 4 — Annotation and Ground Truth

Tasks:
- Susun annotation guideline.
- Identifikasi kandidat yang perlu ditinjau.
- Pisahkan Positive, Negative, Unknown.
- Simpan evidence.
- Review label.
- Evaluasi agreement antar-annotator.

Deliverable:
- Annotation dataset.
- Annotation guideline.
- Label quality report.

## Phase 5 — Baseline Modeling

Tasks:
- Buat baseline sederhana.
- Uji NLP-only.
- Uji temporal-only.
- Uji graph-only.
- Lakukan group split.
- Lakukan temporal split.
- Bandingkan performa.

Deliverable:
- Baseline evaluation report.

## Phase 6 — Advanced Modeling

Tasks:
- Implementasi IndoBERTweet.
- Implementasi LSTM.
- Implementasi GraphSAGE.
- Integrasi feature fusion.
- Hyperparameter tuning.
- Ablation study.
- Error analysis.

Deliverable:
- Trained models.
- Model comparison report.
- Reproducible training pipeline.

## Phase 7 — Inference and Explainability

Tasks:
- Buat inference pipeline.
- Hitung coordination score.
- Tampilkan fitur pendukung.
- Tampilkan bukti kemiripan.
- Tampilkan pola temporal.
- Tampilkan relasi graph.
- Tampilkan uncertainty.
- Sediakan human review.

Deliverable:
- Inference module.
- Explainability report.

## Phase 8 — Application / Dashboard

Tahap ini dilakukan setelah pipeline analisis dan model stabil.

Tasks:
- Dataset upload.
- Analysis configuration.
- Analysis progress.
- Account analysis.
- Network visualization.
- Coordination indicators.
- Evidence panel.
- Report export.

Deliverable:
- CoordinX application prototype.

---

# 16. Recommended Repository Structure

Codex harus menyesuaikan struktur dengan repository yang sudah ada. Struktur berikut merupakan target konseptual, bukan instruksi untuk menghapus struktur lama.

```text
coordinx/
│
├── data/
│   ├── raw/
│   ├── interim/
│   ├── processed/
│   └── annotations/
│
├── notebooks/
│   ├── 01_exploration.ipynb
│   └── 02_pipeline.ipynb
│
├── src/
│   └── coordinx/
│       ├── ingestion/
│       ├── validation/
│       ├── preprocessing/
│       ├── features/
│       │   ├── nlp.py
│       │   ├── temporal.py
│       │   └── graph.py
│       ├── models/
│       │   ├── baseline.py
│       │   ├── indobertweet.py
│       │   ├── temporal_lstm.py
│       │   ├── graphsage.py
│       │   └── fusion.py
│       ├── evaluation/
│       ├── inference/
│       └── reporting/
│
├── configs/
├── tests/
├── artifacts/
├── reports/
├── requirements.txt
├── README.md
└── .gitignore
```

Notebook direncanakan menjadi dua:

1. **Exploration:** eksplorasi data, eksperimen, dan visualisasi.
2. **Pipeline:** proses analisis yang lebih terstruktur dan dapat direproduksi.

Notebook final dirapikan setelah proses eksplorasi dan pengembangan selesai. Hindari membuat ulang notebook final terlalu dini.

---

# 17. Acceptance Criteria

Proyek dianggap memenuhi tahap awal apabila:

1. Dataset dapat dibaca tanpa merusak ID.
2. Dataset raw tidak berubah setelah preprocessing.
3. Duplikasi dapat dideteksi dan dilaporkan.
4. Timestamp dapat divalidasi.
5. Relasi reply dan quote dapat dibentuk menjadi edge.
6. Fitur NLP, temporal, dan graph dapat diekstraksi secara terpisah.
7. Baseline model dapat dilatih dan dievaluasi.
8. Data split tidak menyebabkan kebocoran akun.
9. Unknown tidak dipaksakan menjadi label biner.
10. Setiap hasil model memiliki bukti dan metadata eksperimen.
11. Model dapat diuji pada isu yang berbeda.
12. Semua eksperimen dapat direproduksi.

---

# 18. Instructions for Codex AI Agent

## 18.1 Role

Bertindak sebagai:

- Senior Python Engineer.
- Machine Learning Engineer.
- Data Engineer.
- Research Assistant.

Prioritaskan kualitas data, validitas eksperimen, reproducibility, dan maintainability.

## 18.2 Working Rules

1. Periksa repository sebelum membuat perubahan.
2. Jangan berasumsi semua komponen belum tersedia.
3. Jangan menghapus kode atau file lama tanpa alasan dan persetujuan.
4. Jangan menimpa raw dataset.
5. Jangan mengubah label manual.
6. Jangan mengarang data.
7. Jangan mengarang hasil evaluasi.
8. Jangan mengasumsikan pola yang mencurigakan sebagai bukti pasti koordinasi.
9. Jangan langsung mengimplementasikan IndoBERTweet + LSTM + GraphSAGE sebelum data dan baseline tervalidasi.
10. Gunakan modular architecture.
11. Tambahkan test untuk fungsi yang penting.
12. Dokumentasikan setiap perubahan.
13. Jika terdapat konflik antara implementasi lama dan PRD, jelaskan sebelum melakukan perubahan besar.

## 18.3 Execution Strategy

Bekerja secara bertahap.

Untuk setiap phase:

1. Audit kondisi awal.
2. Jelaskan masalah yang ditemukan.
3. Buat rencana perubahan.
4. Implementasikan bagian yang disepakati.
5. Jalankan test.
6. Laporkan hasil.
7. Dokumentasikan file yang dibuat atau diubah.
8. Tunggu instruksi berikutnya jika perubahan menyentuh keputusan arsitektur atau metodologi yang besar.

Jangan mencoba menyelesaikan seluruh roadmap dalam satu kali perubahan.

## 18.4 First Task — Repository Audit Only

**Tugas pertama Codex adalah melakukan audit repository, bukan langsung coding.**

Periksa:

- Struktur folder.
- File Python.
- Notebook.
- Dataset.
- Dependency.
- Model yang sudah ada.
- Pipeline preprocessing.
- Feature engineering.
- Graph construction.
- Labeling.
- Training.
- Evaluation.
- Output eksperimen.

Kemudian hasilkan:

`reports/REPOSITORY_AUDIT.md`

Dokumen harus berisi:

1. Current project structure.
2. Existing implementation.
3. Working components.
4. Broken or incomplete components.
5. Data quality concerns.
6. Potential data leakage.
7. Modeling concerns.
8. Missing tests.
9. Recommended next steps.
10. Mapping antara kondisi project dan PRD ini.

**Jangan mengubah atau menghapus file project pada tahap pertama.**

---

# 19. Final Product Direction

CoordinX bukan sekadar classifier yang memberikan label buzzer atau organik.

CoordinX harus menjadi sistem analisis yang dapat:

- Menemukan pola kemiripan konten.
- Menemukan pola aktivitas temporal.
- Menemukan hubungan antar-akun.
- Mengidentifikasi kelompok dengan indikasi koordinasi.
- Menyediakan bukti yang dapat diperiksa.
- Mengukur ketidakpastian.
- Mendukung keputusan melalui human review.

**Final principle:**

> CoordinX detects patterns and evidence of potential coordinated inauthentic behavior. It does not automatically determine the identity, affiliation, motive, or funding of an account.

Fokus pengembangan adalah menghasilkan sistem yang dapat dipertanggungjawabkan secara teknis dan metodologis, bukan sekadar mendapatkan angka akurasi tinggi.