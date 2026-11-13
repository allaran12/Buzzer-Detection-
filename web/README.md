# CoordinX Web Dashboard

Frontend dashboard untuk **CoordinX: AI-Powered Coordinated Behavior & Buzzer Detection System**.

Dibuat menggunakan **Next.js (App Router)**, **TypeScript**, dan **Tailwind CSS**. Siap dideploy langsung ke **Vercel**.

---

## Fitur Utama

- **Analisis live:** Menerima URL posting, URL hashtag, URL pencarian, hashtag, dan keyword biasa; maksimal 500 postingan terbaru melalui `twscrape`.
- **Tiga branch model:** IndoBERTweet, Temporal LSTM, dan GraphSAGE digabungkan melalui skor fusion.
- **Evidence:** Menampilkan skor risiko, status review, kemiripan teks, burst, relasi graph berarah, hub, frasa berulang, sentiment indikatif, profil/avatar, dan warning keterbatasan sampel.
- **Admin scraper:** Mengatur cookie `auth_token` dan `ct0` tanpa menyimpan kredensial X di browser frontend.

---

## Cara Menjalankan Secara Lokal

Instal dependency backend dari root repository:

```bash
python -m pip install -r requirements-web-backend.txt
```

Jalankan backend dari root repository:

```bash
PYTHONPATH=. uvicorn services.inference_api.main:app --host 127.0.0.1 --port 8000
```

Di terminal lain, jalankan frontend dari direktori `web/`:

```bash
cd web
npm ci
npm run dev
```

Buka [http://localhost:3000](http://localhost:3000) di browser Anda.

Frontend memakai backend lokal `http://127.0.0.1:8000` saat development. Untuk backend di host lain, set `FASTAPI_BACKEND_URL` pada environment frontend. Endpoint admin memakai `COORDINX_ADMIN_TOKEN`; default backend lokalnya `local-admin` (wajib diganti pada production). Buka `/admin/scraper`, masukkan token admin, lalu masukkan `auth_token` dan `ct0` dari cookie sesi X; username/password X tidak dikirim atau disimpan oleh frontend.

Session yang disimpan lewat `/admin/scraper` berlaku global untuk semua user yang mengakses instance FastAPI dan `COORDINX_SCRAPER_DB` yang sama. Penggantian session langsung dipakai pada request berikutnya karena scraper membaca database bersama setiap kali melakukan scraping. Ini tidak berlaku lintas instance backend yang memakai database berbeda. `COORDINX_SCRAPER_COOKIES` hanya dipakai sebagai bootstrap ketika database belum ada; setelah admin menyimpan session, nilainya tidak menimpa session admin.

Pada production, set `COORDINX_SCRAPER_DB` ke lokasi writable di luar repository, misalnya `/var/lib/coordinx/accounts.db`. Tanpa variable tersebut, backend production mencoba `~/.coordinx/accounts.db` dan akan fail-fast bila lokasi itu tidak writable; database yang tersimpan di checkout repository tidak dipakai. Rotasi cookie X jika pernah masuk Git atau log.

Backend memakai `COORDINX_HF_LOCAL_ONLY=true` secara default agar request produksi tidak mencoba mengunduh checkpoint IndoBERTweet. Saat deploy, preload cache `indolem/indobertweet-base-uncased` pada image/server; gunakan `COORDINX_HF_LOCAL_ONLY=false` hanya pada proses bootstrap yang memang memiliki akses jaringan.

Pencarian live dapat berupa:

- `https://x.com/user/status/123...`
- `https://x.com/hashtag/topik`
- `https://x.com/search?q=topik`
- `#topik` atau keyword biasa

UI menyediakan pilihan 100, 250, atau 500 postingan terbaru tanpa pembatas waktu default. Sentimen memakai `lexicon-live-v1` sebagai konteks tambahan dan tidak memengaruhi skor fusion. API masih menerima `days` bila analisis perlu dibatasi ke rentang tertentu.

Jika URL valid tetapi scraping gagal, backend mencoba sampel lokal yang relevan untuk topik yang tersedia (`RoySuryo`, `prayforkalimantan`, `wowo2`, `jokowi`, `riaricis`, atau `wowo`) dan menandai response dengan `source: local_dataset_fallback` serta warning yang transparan. Untuk topik lain, pastikan akun aktif di `accounts.db` dan session cookie sudah diatur melalui `/admin/scraper`. Skor adalah indikasi koordinasi untuk human review, bukan vonis bahwa akun pasti buzzer.

---

## Cara Deploy ke Vercel

1. Push kode frontend ke GitHub; jangan commit cookie, cache Hugging Face, atau model besar.
2. Deploy `web/` ke Vercel dan set `FASTAPI_BACKEND_URL` ke backend FastAPI yang dapat dijangkau server-side.
3. Deploy backend Python dan akun `twscrape` secara terpisah; Vercel hanya menjalankan proxy/UI, bukan scraper atau model PyTorch.

Untuk production, set minimal `COORDINX_ENV=production`, `COORDINX_ADMIN_TOKEN`, `COORDINX_CORS_ORIGINS`, `COORDINX_HF_LOCAL_ONLY=true`, dan `FASTAPI_BACKEND_URL`. Jangan commit `accounts.db`, cookie X, atau cache Hugging Face ke GitHub.

## Deploy FastAPI ke Railway

Repository sudah menyediakan `Dockerfile` dan `railway.toml`. Railway akan memakai Dockerfile di root repository; image menginstal dependency backend, membawa tiga artifact model final, dan melakukan preload cache IndoBERTweet saat build.

1. Buat satu service Railway dari repository ini. Biarkan root directory di `/` agar `Dockerfile` dan `railway.toml` terbaca.
2. Tambahkan persistent volume dengan mount path `/data` dan set `COORDINX_SCRAPER_DB=/data/accounts.db`. Database session X tidak boleh diletakkan di image atau checkout Git.
3. Set variables berikut pada service:
   - `COORDINX_ENV=production`
   - `COORDINX_ADMIN_TOKEN=<random-long-secret>`
   - `COORDINX_CORS_ORIGINS=https://<domain-vercel>`
   - `COORDINX_HF_LOCAL_ONLY=true`
   - `COORDINX_SCRAPER_DB=/data/accounts.db`
   - `COORDINX_SCRAPE_TIMEOUT_SECONDS=240`
4. Healthcheck memakai `/api/v1/health`; port aplikasi mengikuti `$PORT` dari Railway.
5. Setelah deployment aktif, buka `https://<domain-vercel>/admin/scraper` dan simpan `auth_token` serta `ct0` sekali. Semua user kemudian memakai session yang sama melalui backend.
6. Gunakan satu replica selama memakai SQLite volume. Jika perlu scale horizontal, pindahkan session store ke storage bersama yang mendukung multi-instance sebelum menambah replica.

### Status kesiapan

- Vercel: siap secara teknis setelah Root Directory diatur ke `web` dan `FASTAPI_BACKEND_URL` diisi.
- Railway: siap dibuild/deploy setelah volume dan variables production diisi.
- Belum aman untuk push production sebelum dua file `screpping/accounts.db` yang pernah terlacak Git dilepas dari index dan cookie X yang pernah tersimpan di dalamnya dirotasi.
