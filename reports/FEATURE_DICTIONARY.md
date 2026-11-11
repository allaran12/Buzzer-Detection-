# COORDINX — CANONICAL FEATURE DICTIONARY
**PRD Phase 3 Deliverable**  
**Schema:** `canonical-v1`  
**Dataset:** Batch 2 (`wowo2`) dan Batch 3 (`RoySuryo`)

Semua file fitur Batch 2 dan Batch 3 dibuat dari `data/processed/*/standardized_data.csv` dengan generator yang sama: `src/features/canonical_features.py`.

## 1. Post-Level Features

File: `data/features/{batch}_posts_with_features.csv`

| Feature | Tipe | Deskripsi |
|---|---|---|
| `post_id` | String | ID unik postingan; selalu dipertahankan sebagai string |
| `account_id` | String | ID akun penulis |
| `dataset_id` | String | `batch2` atau `batch3` |
| `issue_id` | String | `wowo2` atau `RoySuryo` |
| `text` | String | Teks asli dari standardized data |
| `body_clean` | String | Teks setelah URL dan mention dihapus |
| `text_model_input` | String | Input teks proxy yang dipakai model |
| `hashtags` | JSON string | Daftar hashtag |
| `n_tags` | Integer | Jumlah hashtag |
| `body_len` | Integer | Panjang `body_clean` |
| `has_url` | Integer | Indikator URL |
| `date` | Datetime UTC | Waktu posting |
| `date_only` | String | Tanggal UTC |
| `relation_type` | String | `original`, `reply`, atau `quote` |
| `target_account_id` | String | ID target reply/quote jika tersedia/resolvable |

## 2. Account-Level Features

File: `data/features/{batch}_account_features.csv`

### Identitas dan aktivitas

| Feature | Deskripsi |
|---|---|
| `account_id` | ID akun canonical |
| `username` | Username yang terlihat pada dataset |
| `dataset_id`, `issue_id` | Metadata dataset dan isu |
| `n_posts` | Jumlah postingan |
| `n_originals`, `n_replies`, `n_quotes` | Komposisi jenis postingan |
| `followers`, `following`, `follower_ratio` | Metadata audiens |
| `avg_tags`, `avg_body_len`, `url_rate`, `avg_words` | Agregat konten |

### Temporal

| Feature | Deskripsi |
|---|---|
| `first_post`, `last_post` | Batas waktu aktivitas |
| `active_hours` | Selisih jam postingan pertama dan terakhir |
| `post_rate` | Postingan per jam aktif; satu-post memakai nilai legacy `10.0` |
| `sequence_len` | Panjang urutan posting |
| `mean_interval_hours`, `std_interval_hours` | Statistik interval antarpost |
| `min_interval_hours`, `max_interval_hours` | Interval minimum dan maksimum |
| `burst_ratio_1h` | Proporsi interval <= 1 jam |
| `active_span_hours_observed` | Active span yang teramati |
| `active_days_observed` | Jumlah hari aktif |
| `hour_entropy` | Entropi distribusi jam posting |

### Graph

| Feature | Deskripsi |
|---|---|
| `in_degree` | Jumlah target unik yang mengarah ke akun |
| `out_degree` | Jumlah target unik yang dituju akun |
| `total_degree` | `in_degree + out_degree` |
| `pagerank` | PageRank graph terarah |
| `component_size` | Ukuran komponen terhubung |
| `graph_in_degree`, `graph_out_degree` | Alias graph eksplisit untuk model |
| `graph_unique_targets`, `graph_unique_sources` | Jumlah tetangga unik |
| `graph_pagerank`, `graph_component_size` | Alias metrik graph untuk model |

`data/features/{batch}_interactions.csv` menyimpan event reply/quote, termasuk event self-loop yang ditandai `is_valid_edge=False` untuk audit. Metrik graph memakai edge valid tanpa self-loop.

## 3. Score dan Metadata Label

File: `data/features/{batch}_account_features_with_scores.csv`

- `score_post_rate`, `score_high_tags`, `score_body_length`, `score_out_degree`, dan `score_low_follower_ratio` adalah komponen heuristic.
- `buzzer_score` hanya alat bantu review; bukan ground truth dan tidak digunakan sebagai fitur model.
- `label` hanya terisi untuk akun yang sudah dianotasi.
- `evidence`, `notes`, `review_status`, `candidate_type`, dan `label_source` adalah metadata anotasi.
- File canonical label tersimpan di `data/labels/{batch}_labeled_canonical.csv`; nilai manual `label` tidak diubah.

## 4. Validation

`data/features/{batch}_validation.json` mencatat jumlah post, akun, ID unik, relation type, edge event, unique directed edge, self-loop, target unresolved, dan preservasi label.
