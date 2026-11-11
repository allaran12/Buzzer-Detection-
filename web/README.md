# CoordinX Web Dashboard

Frontend dashboard untuk **CoordinX: AI-Powered Coordinated Behavior & Buzzer Detection System**.

Dibuat menggunakan **Next.js (App Router)**, **TypeScript**, dan **Tailwind CSS**. Siap dideploy langsung ke **Vercel**.

---

## Fitur Utama

- **KPI Overview:** Metrik ringkasan akun teranalisis, persentase akun risiko tinggi (buzzer), risiko sedang, dan akun organik.
- **Aktivitas Temporal & Burst Chart:** Visualisasi lonjakan volume postingan per jam yang membedakan aktivitas organik dengan aktivitas buzzer serentak.
- **Account Risk Inspector & Interactive Table:**
  - Filter kategori risiko (Semua, Risiko Tinggi 🔴, Potensi Terkoordinasi 🟡, Akun Organik 🟢).
  - Filter berdasarkan kampanye/isu (#PrayForKalimantan, Pilpres wowo2, RoySuryo, dll.).
  - Pencarian cepat berdasarkan username, nama, atau bio.
  - Sorting berdasarkan Buzzer Score, Followers, Post Rate, dll.
- **Modal Inspeksi Mendalam Akun:**
  - Dekomposisi skor 4 pilar AI (NLP Semantik IndoBERTweet, Temporal Burst, Topologi Graf Out-Degree, Anomali Profil).
  - Sampel tweet interaktif lengkap dengan relasi (reply, quote, retweet, original), timestamp, dan indikator kesamaan teks.
- **Simulasi Analisis URL Baru:** Input URL postingan X atau tagar untuk memicu pipeline deteksi.

---

## Cara Menjalankan Secara Lokal

Pastikan Anda berada di direktori `web/`:

```bash
cd web
npm install
npm run dev
```

Buka [http://localhost:3000](http://localhost:3000) di browser Anda.

---

## Cara Deploy ke Vercel

1. Push repository ke GitHub.
2. Buka dashboard [Vercel](https://vercel.com/) dan impor repository ini.
3. Atur **Root Directory** ke `web`.
4. Klik **Deploy**. Vercel akan otomatis mendeteksi konfigurasi Next.js dan mendeploy aplikasi dalam hitungan detik.
