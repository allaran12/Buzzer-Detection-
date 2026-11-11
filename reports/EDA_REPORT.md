# COORDINX — EXPLORATORY DATA ANALYSIS (EDA) REPORT
**Phase:** PRD Phase 2  
**Dataset:** `data/processed/RoySuryo/standardized_data.csv`  
**Analyzed Posts:** 1,081  
**Analyzed Accounts:** 796  

---

## 1. Distribusi Postingan & Relasi
- **Total Postingan Bersih:** 1081
- **Akun Unik:** 796
- **Komposisi Interaksi:**
  - `reply`: 621 (57.4%)
  - `original`: 344 (31.8%)
  - `quote`: 116 (10.7%)

> **Insight:** Reply (621) mendominasi dataset, menandakan percakapan bersifat interaktif dan reaktif terhadap suatu isu viral.

---

## 2. Karakteristik Aktivitas Akun
- **Akun dengan hanya 1 postingan:** 662 akun (83.2%)
- **Akun aktif (>1 postingan):** 134 akun (16.8%)
- **Rata-rata postingan per akun:** 1.36 post
- **Top Akun Teraktif:**
  1. `@eka2_suprianto`: 29 postingan
  1. `@bobidasaya`: 13 postingan
  1. `@aerobzik`: 12 postingan
  1. `@skievsy`: 10 postingan
  1. `@INRI2025`: 9 postingan

> **Insight:** Extreme skew. Lebih dari 70% akun hanya berpartisipasi satu kali. Analisis temporal perlu memperlakukan akun satu kali posting secara khusus agar metrik burst tidak terdistorsi.

---

## 3. Distribusi Waktu (Temporal Activity)
- **Zona Waktu:** UTC dikonversi ke WIB (Asia/Jakarta, UTC+7).
- **Puncak Aktivitas Jam:** Jam 18:00 WIB (85 postingan).
- **Deteksi Burst Activity:**
  - Terdapat 24 jendela 1-jam di mana satu akun mengunggah $\ge 3$ postingan.
  - Akun burst teratas: `@eka2_suprianto` (13 post/jam).

---

## 4. Analisis Kemiripan Narasi & Sinkronisasi Waktu
- **Pasangan kemiripan teks $\ge 0.60$ antar-akun berbeda:** 242 pasangan terdeteksi.
- **Top Pasangan Teks Tersinkronisasi:**
  - `@parjo4423939442` & `@ArdieSuhardi321` (Sim: 1.0, Jarak: 610.5 menit)
    Snippet: "WONG PALSU KOK DITUNJUKKAN....

ROY SURYO SINDIR JOKOWI USAI IJAZAH DIPERLIHATKA..."
  - `@parjo4423939442` & `@ArdieSuhardi321` (Sim: 1.0, Jarak: 609.1 menit)
    Snippet: "WONG PALSU KOK DITUNJUKKAN....

ROY SURYO SINDIR JOKOWI USAI IJAZAH DIPERLIHATKA..."
  - `@CocoLatii` & `@matdjempol22756` (Sim: 1.0, Jarak: 1626.1 menit)
    Snippet: "to jumianto..... ngefans roy suryo tibake 😁..."

> **Insight:** Ditemukan kemiripan teks tinggi dengan selisih waktu menit antar-akun berbeda. Ini adalah indikator kuat pola *copy-paste coordination*.

---

## 5. Analisis Jaringan Interaksi (Network Graph)
- **Node interaksi:** 890 akun
- **Edge interaksi (reply/quote):** 716 relasi
- **Weakly Connected Components:** 205 kelompok
- **Komponen Terbesar:** 323 akun terhubung
- **Akun Paling Banyak Menyerang/Membalas (Out-Degree):**
  - `1659058096659136513`: 25 balasan/kutipan
  - `1979047796809355264`: 11 balasan/kutipan
  - `2096603479100043264`: 8 balasan/kutipan
- **Akun Paling Banyak Ditarget (In-Degree):**
  - `1389107518702374915`: 22 kali dibalas/dikutip
  - `2002820059648212992`: 22 kali dibalas/dikutip
  - `3007567602`: 18 kali dibalas/dikutip

---

## Visualisasi Tersimpan
- `output/eda/eda_activity_distribution.png`
- `output/eda/eda_hourly_wib.png`
- `output/eda/eda_top_hashtags.png`
