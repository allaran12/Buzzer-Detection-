# COORDINX — FEATURE EXPLORATION REPORT
**Phase:** PRD Phase 2 (Bridge to Phase 3 Feature Engineering)  
**Reference:** `PRD.md` Section 8

Berdasarkan temuan EDA, fitur-fitur berikut direkomendasikan untuk diekstraksi pada Phase 3:

### 1. Level Postingan (NLP & Content)
- `narrative_len`: Panjang karakter teks setelah mention/URL dibersihkan.
- `n_hashtags`: Jumlah hashtag yang dipakai.
- `has_url`: Keberadaan URL link.
- `max_text_similarity`: Skor kemiripan teks tertinggi postingan ini dengan postingan akun lain.

### 2. Level Akun (Temporal & Activity)
- `post_rate`: Kecepatan postingan per jam aktif (diberi penalti/normalisasi untuk akun 1 post).
- `burst_frequency`: Frekuensi akun melakukan $\ge 3$ postingan dalam jendela 1 jam.
- `follower_ratio`: Rasio followers terhadap following ($followers / (following + 1)$).
- `reply_quote_ratio`: Persentase postingan yang merupakan reply/quote vs original.

### 3. Level Jaringan (Graph Topology)
- `in_degree`: Seberapa sering akun dijadikan target interaksi.
- `out_degree`: Seberapa agresif akun membalas/mengutip akun lain.
- `pagerank`: Bobot pengaruh akun dalam graf interaksi.
- `component_size`: Ukuran klaster terhubung tempat akun bernaung.
