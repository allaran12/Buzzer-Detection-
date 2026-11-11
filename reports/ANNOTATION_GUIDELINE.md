# COORDINX — ANNOTATION GUIDELINE
**PRD Phase 4 Deliverable**  
**Reference:** `PRD.md` Section 10 (Labeling and Ground Truth)

---

## 1. Prinsip Utama Anotasi
- Label **BUKAN** ditentukan oleh kesamaan opini, nama tokoh yang dibahas, atau sentimen politik.
- Label **BUKAN** ditentukan hanya oleh satu metrik (misal follower sedikit atau hashtag banyak).
- Anotasi bertujuan membedakan perilaku terkoordinasi tidak autentik (*coordinated inauthentic*) dari interaksi wajar (*organic netizen*).

## 2. Definisi Kategori Label

### A. Positive (`1` — Coordinated Buzzer)
Diberikan jika memenuhi minimal 2 kriteria berikut:
1. **Duplikasi / Template:** Mengunggah narasi teks yang identik atau sangat mirip dengan akun lain dalam rentang waktu berdekatan.
2. **Interaksi Anomali:** Akun hanya aktif membalas/mengutip target tertentu secara berulang tanpa variasi topik pribadi.
3. **Perilaku Burst:** Mengirim banyak tweet dalam satu jendela waktu singkat untuk mengamplifikasi hashtag/isu tertentu.

### B. Negative (`0` — Organic User)
Diberikan jika:
1. Teks merupakan opini personal, bervariasi, dan menggunakan gaya bahasa alami.
2. Akun memiliki riwayat interaksi dua arah yang wajar dengan pengguna lain.
3. Tidak ada indikasi koordinasi waktu atau penggunaan template copy-paste massal.

### C. Unknown (`-1` / Pending)
1. Bukti belum cukup (misal akun hanya memiliki 1 tweet tanpa template yang jelas).
2. **DILARANG** memaksakan status Unknown menjadi Positive atau Negative jika bukti tidak konklusif.

## 3. Skema Kolom Anotasi
Setiap baris berlabel wajib memuat:
- `account_id` / `username`: Identitas akun.
- `label`: `1` (Positive), `0` (Negative), atau `NaN` (Unknown).
- `evidence`: Ringkasan bukti pengamatan (misal: template, out-degree, timing).
- `review_status`: `VERIFIED` atau `PENDING`.
