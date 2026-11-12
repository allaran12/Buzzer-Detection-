# CoordinX Web Dashboard

Frontend dashboard untuk **CoordinX: AI-Powered Coordinated Behavior & Buzzer Detection System**.

Dibuat menggunakan **Next.js (App Router)**, **TypeScript**, dan **Tailwind CSS**. Siap dideploy langsung ke **Vercel**.

---

## Fitur Utama

- **Analisis URL live:** Mengambil posting target dan balasan publik melalui `twscrape`.
- **Tiga branch model:** IndoBERTweet, Temporal LSTM, dan GraphSAGE digabungkan melalui skor fusion.
- **Evidence:** Menampilkan skor risiko, status review, kemiripan teks, burst, relasi graph, frasa berulang, dan warning keterbatasan sampel.
- **Admin scraper:** Mengatur cookie `auth_token` dan `ct0` tanpa menyimpan kredensial X di browser frontend.

---

## Cara Menjalankan Secara Lokal

Instal dependency backend dari root repository:

```bash
python -m pip install -r requirements-web-backend.txt
```

Jalankan backend dari root repository:

```bash
uvicorn src.api_service:app --host 127.0.0.1 --port 8000
```

Di terminal lain, jalankan frontend dari direktori `web/`:

```bash
cd web
npm ci
npm run dev
```

Buka [http://localhost:3000](http://localhost:3000) di browser Anda.

Frontend memakai backend lokal `http://127.0.0.1:8000` saat development. Untuk backend di host lain, set `FASTAPI_BACKEND_URL` pada environment frontend. Endpoint admin memakai `COORDINX_ADMIN_TOKEN`; default lokalnya `local-admin`.

Jika URL valid tetapi scraping gagal, pastikan akun aktif di `screpping/accounts.db` dan session cookie sudah diatur melalui `/admin/scraper`. Skor adalah indikasi koordinasi untuk human review, bukan vonis bahwa akun pasti buzzer.

---

## Cara Deploy ke Vercel

1. Push kode frontend ke GitHub; jangan commit cookie, cache Hugging Face, atau model besar.
2. Deploy `web/` ke Vercel dan set `FASTAPI_BACKEND_URL` ke backend FastAPI yang dapat dijangkau server-side.
3. Deploy backend Python dan akun `twscrape` secara terpisah; Vercel hanya menjalankan proxy/UI, bukan scraper atau model PyTorch.
