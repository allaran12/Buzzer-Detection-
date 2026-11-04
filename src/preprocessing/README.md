# CoordinX preprocessing

## Struktur
- `data/raw/`: simpan CSV mentah hasil scraping di sini.
- `data/interim/`: hasil Data Cleaning.
- `data/processed/`: hasil Data Standardization.
- `src/preprocessing/`: script preprocessing.

## Menjalankan
Dari root project:

```bash
pip install pandas
python src/preprocessing/cleaning.py --input data/raw/prayforkalimantan.csv
python src/preprocessing/standardization.py
```

Jika nama/lokasi CSV berbeda, sesuaikan argumen `--input` pada perintah cleaning.

## Prinsip
- File raw tidak diubah.
- Duplikasi berdasarkan `post_id` disimpan terpisah di `duplicate_posts.csv`.
- Baris dengan teks kosong atau identitas post/akun kosong disimpan terpisah di `rejected_rows.csv`.
- Original, reply, quote, dan retweet tidak dihapus hanya karena jenis relasinya.
- Bio kosong dan target relasi kosong pada post original diperbolehkan.
- ID dibaca sebagai string agar tidak kehilangan presisi.
- Teks tidak dihapus hashtag, URL, emoji, atau mention karena masih relevan untuk analisis.
