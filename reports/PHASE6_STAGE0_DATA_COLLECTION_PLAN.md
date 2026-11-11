# Phase 6 Stage 0 - Environment and Data Collection Plan

## Status

Stage 0 sudah dijalankan melalui `notebooks/06_stage0_environment_data_readiness.ipynb`.

- Canonical data contract: lulus.
- Data raw: tidak diubah.
- Label manual: tidak diubah.
- `buzzer_score`: tidak dipakai sebagai fitur atau ground truth.
- Environment deep learning: siap CPU-only; `torch`, `transformers`, dan `torch_geometric` sudah terpasang.
- CUDA: tidak tersedia pada environment aktif; training akan berjalan di CPU.

Environment manifest:

- `requirements-phase6-deep-learning.txt`

Smoke test yang lulus:

- `torch==2.15.0+cpu`
- `transformers==5.22.2`
- `torch-geometric==2.8.1`
- `accelerate==1.15.0`
- `sentencepiece==0.2.3`
- `safetensors==0.8.0`
- `torch.cuda.is_available() == False`

Readiness JSON:

- `output/phase6_stage0/stage0_readiness.json`

## Inventaris Saat Ini

| Metrik | Batch 2 | Batch 3 | Total |
|---|---:|---:|---:|
| Post | 1,514 | 1,081 | 2,595 |
| Akun | 1,007 | 796 | 1,803 |
| Akun berlabel | 50 | 50 | 100 |
| Organic | 27 | 21 | 48 |
| Buzzer | 23 | 29 | 52 |
| Akun multi-post | 168 | 134 | 302 |
| Akun berlabel multi-post | 10 | 10 | 20 |
| Edge valid | 651 | 714 | 1,365 |

## Target Pengumpulan

Angka berikut adalah target engineering untuk mengurangi risiko overfitting, bukan jaminan performa model.

### Minimum Prototype

Target minimum sebelum menyebut tiga branch sebagai prototype yang dapat dibandingkan:

- 300 akun berlabel total.
- Minimal 150 Organic dan 150 Buzzer.
- Minimal 100 akun berlabel multi-post.
- Minimal 50 akun multi-post per kelas jika memungkinkan.
- Minimal 1,500 edge valid.
- Label tersebar di setiap issue, bukan hanya terkumpul pada satu issue.

Gap dari data sekarang:

- Tambah 200 akun berlabel.
- Tambah sekurang-kurangnya 102 Organic dan 98 Buzzer untuk mencapai keseimbangan kelas minimum.
- Tambah 80 akun berlabel multi-post.
- Tambah 135 edge valid.

### Recommended Stable Comparison

Target yang lebih aman untuk membandingkan IndoBERTweet, LSTM, GraphSAGE, dan fusion:

- 600 akun berlabel total.
- Minimal 300 Organic dan 300 Buzzer.
- Minimal 200 akun berlabel multi-post.
- Minimal 100 akun multi-post per kelas jika memungkinkan.
- Minimal 3,000 edge valid.
- Masing-masing issue memiliki label dua kelas yang cukup untuk cross-issue evaluation.

Gap dari data sekarang:

- Tambah 500 akun berlabel.
- Tambah sekurang-kurangnya 252 Organic dan 248 Buzzer.
- Tambah 180 akun berlabel multi-post.
- Tambah 1,635 edge valid.

## Prioritas Berdasarkan Algoritma

### IndoBERTweet

- Dapat mulai diuji dengan 100 label menggunakan frozen encoder.
- Untuk fine-tuning penuh, target 600 label lebih aman.
- Teks post harus mempertahankan hashtag, emoji, mention, URL marker, dan gaya bahasa yang relevan.
- Pooling ke level akun harus menyimpan `account_id` dan `post_id` sebagai metadata.

### Temporal LSTM

- Prioritas pengumpulan adalah akun yang memiliki minimal 3 post.
- Akun satu post tidak memberi informasi urutan yang cukup untuk LSTM.
- Label multi-post saat ini baru 20; minimum prototype membutuhkan tambahan 80.
- Timestamp harus valid dan urutan post harus dapat direkonstruksi.

### GraphSAGE

- Pertahankan edge reply/quote yang valid.
- Jangan hanya mengumpulkan akun; kumpulkan juga target reply/quote yang dapat dipetakan ke node.
- Tambahkan label pada node yang terhubung dan node isolated agar evaluasi tidak bias.
- Simpan `source_account_id`, `target_account_id`, `relation_type`, `edge_id`, `issue_id`, dan timestamp.

## Aturan Labeling Batch Berikutnya

1. Seimbangkan Organic dan Buzzer sedekat mungkin.
2. Pastikan setiap issue memiliki kedua kelas.
3. Prioritaskan akun multi-post untuk label manual.
4. Sertakan akun dengan edge graph dan sebagian akun tanpa edge sebagai kontrol.
5. Simpan evidence dan notes untuk setiap label.
6. Jangan mengubah label lama tanpa audit perubahan.
7. Jalankan cleaning, standardization, feature regeneration, dan validasi canonical setelah batch baru masuk.

## Urutan Setelah Data Cukup

1. Pasang dan catat environment `torch`, `transformers`, dan `torch_geometric`.
2. Jalankan frozen IndoBERTweet sebagai branch pertama.
3. Jalankan Temporal LSTM pada subset akun multi-post.
4. Jalankan GraphSAGE pada graph gabungan dengan split yang mencegah leakage.
5. Bandingkan setiap branch dengan fusion proxy lama.
6. Bangun fusion menggunakan out-of-fold prediction.
7. Update Phase 7 hanya setelah model baru lulus evaluasi group, temporal, dan cross-issue.
8. Baru lanjutkan dashboard Phase 8 menggunakan schema inference yang sudah stabil.
