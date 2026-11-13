# Final Audit Report

Tanggal audit terakhir: 2026-11-13

## 1. Ringkasan proyek

CoordinX adalah sistem deteksi perilaku terkoordinasi dengan:

- Frontend: Next.js 16, React 19, TypeScript, Tailwind.
- Backend canonical: FastAPI pada `services.inference_api.main`.
- Inference: pandas, scikit-learn, model artifacts pickle/PyTorch.
- Scraping/account session: twscrape dan SQLite.
- Data: dataset CSV, feature pipeline, model registry.

Modul utama yang diaudit: `web/src`, `services/inference_api`, `src/inference`, `src/screpping.py`, API proxy Next.js, tests, manifest dependency, dan konfigurasi Git.

## 2. Hasil audit

Audit read-only mencakup struktur repository, Git state, dokumentasi, source frontend/backend, API routes, model adapter, account manager, database path, tests, dependency manifest, lint, build, dan runtime route inspection.

Status modul:

- Frontend rendering/build: berfungsi; tab graf, sentimen, bukti teks, dan avatar terisi dari response API.
- Canonical FastAPI startup/import: berfungsi dengan `services.inference_api.main:app`.
- Admin account API: berfungsi dan terlindungi token.
- Account validation: diperbaiki dan diuji untuk cookie, password, serta input parsial.
- Model adapter probability handling: diperbaiki dan diuji untuk class ordering terbalik.
- Frontend API proxy: berfungsi dan menghasilkan kontrak yang sama dengan backend untuk dataset live/fallback.
- Test suite: 16 unit/regression test lulus dengan `unittest`; compile, typecheck, lint, dan production build lulus.
- Legacy `src/api_service.py`: menjadi compatibility wrapper yang me-re-export app canonical.

## 3. Masalah dan solusi

| Prioritas | File/lokasi | Masalah | Solusi |
|---|---|---|---|
| P1 | `services/inference_api/main.py` | Backend tidak memiliki `/api/v1/accounts` yang dipakai frontend | Menambahkan canonical compatibility route |
| P1 | `services/inference_api/main.py` | Request analisis menerima cookie caller dan endpoint live tidak terproteksi | Model request kini menolak field ekstra; live analysis membutuhkan admin token dan cookie tidak diteruskan |
| P1 | `services/inference_api/main.py` | Handler exception duplikat/unreachable | Menghapus handler duplikat |
| P1 | `services/inference_api/main.py` | Auth production dapat memakai fallback predictable | Fallback hanya berlaku pada environment development; production membutuhkan `COORDINX_ADMIN_TOKEN` |
| P1 | `services/inference_api/account_manager.py` | Validasi cookie mematikan jalur password; cookie tidak diverifikasi | Mendukung cookie lengkap atau kredensial password lengkap, memakai username stabil, memanggil login, dan memeriksa status akun |
| P1 | `src/inference/model_adapter.py` | Probabilitas selalu mengambil kolom kedua | Menggunakan `classes_` untuk mencari label `1` |
| P2 | `web/src/app/admin/scraper/page.tsx` | Error non-JSON/network menjadi unhandled rejection | Menambahkan error handling dan pembersihan form di `finally` |
| P1 sebelumnya | `src/inference/live_pipeline.py` | Import menunjuk `src.screpping.screpping` yang tidak valid | Diperbaiki menjadi `src.screpping` sebelum audit ini |
| P1 | `services/inference_api/main.py` | Scraping X gagal sebelum payload analisis dikirim ke UI | Menambahkan fallback dataset lokal relevan dengan source dan warning transparan |
| P1 | `services/inference_api/main.py` | URL status lokal tidak selalu memiliki ID pada snapshot | Menambahkan resolusi berdasarkan post ID lalu username akun terkait |
| P1 | `src/api_service.py` | Entrypoint lama memakai kontrak backend berbeda | Mengubahnya menjadi wrapper ke app canonical |

## 4. Perubahan

File baru:

- `tests/test_canonical_api.py`
- `tests/test_account_manager.py`
- `tests/test_model_adapter.py`
- `docs/superpowers/plans/2026-11-12-backend-consolidation-audit.md`
- `FINAL_AUDIT_REPORT.md`

File dimodifikasi:

- `services/inference_api/main.py`
- `services/inference_api/account_manager.py`
- `src/inference/model_adapter.py`
- `web/src/app/admin/scraper/page.tsx`
- `src/inference/live_pipeline.py` (perbaikan sebelumnya dalam sesi)
- `src/api_service.py`
- `web/README.md`
- `services/inference_api/LIVE_COLLECTION.md`

Perubahan tidak menghapus database, tabel, model, atau data pengguna.

## 5. Hasil pengujian

| Pengujian | Perintah | Hasil |
|---|---|---|
| Python compile | `.venv-final/bin/python -m compileall -q src services tests` | PASS |
| Regression tests | `.venv-final/bin/python -m unittest discover -s tests -q` | PASS: 16/16 |
| Canonical route smoke test | import app dan assert route | PASS |
| Dependency consistency | `python -m pip check` | PASS: No broken requirements |
| Frontend lint | `npm run lint` | PASS tanpa error |
| Typecheck | `./node_modules/.bin/tsc --noEmit` | PASS |
| Production build | `npm run build` | PASS |
| API direct/proxy E2E | POST `/api/v1/analyze` dan `/api/analyze` | PASS: graf, sentimen, evidence, frasa, avatar |
| Browser UI E2E | query `#RoySuryo` | PASS: semua tab hasil terlihat dan terisi |
| Live X scraping E2E | session twscrape lokal | BLOCKED oleh `No account available for queue ...`; fallback aktif |

## 6. Masalah tersisa dan keterbatasan

1. Akun X/twscrape lokal masih timeout atau tidak mendapat queue pada sebagian endpoint X; ini masalah akses eksternal, bukan kontrak UI. Known dataset memakai fallback lokal dengan warning.
2. Untuk production, tetap diperlukan session X yang valid, `COORDINX_ADMIN_TOKEN`, dan `COORDINX_SCRAPER_DB` writable.
3. Fallback lokal hanya memetakan topik yang tersedia atau URL status yang akun/post-nya ada di snapshot; topik lain mengembalikan error yang eksplisit dan tidak memalsukan hasil.
4. Model artifacts pickle/PyTorch tetap membutuhkan trusted deployment artifacts. Jangan memuat artifact dari sumber tidak terpercaya.

## 7. Keamanan

- Production harus mengatur `COORDINX_ADMIN_TOKEN`; token default tidak dipakai pada environment production.
- Cookie caller di endpoint analysis publik telah ditolak.
- Status account API tidak mengembalikan field cookie.
- Dataset path tetap dibatasi ke direktori `data` oleh feature builder.
- Database dan credential file tidak dihapus. Credential yang pernah tersimpan harus dianggap sensitif dan dirotasi bila pernah terekspos.

## 8. Kesimpulan

**READY WITH LIMITATIONS**

Sistem canonical berhasil melewati compile, 16 regression tests, route smoke test, frontend typecheck, lint, production build, API direct/proxy E2E, dan browser UI E2E. Satu keterbatasan operasional tetap ada: akses live X/twscrape bergantung pada session dan queue eksternal; saat layanan itu gagal, sistem sekarang mengembalikan dataset lokal relevan secara transparan sehingga graf, sentimen, bukti teks, dan avatar tetap muncul.
