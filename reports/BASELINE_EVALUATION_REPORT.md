# COORDINX - PHASE 5 BASELINE EVALUATION REPORT

**Generated (UTC):** 2026-11-09
**Notebook:** `notebooks/04b_supervised_baseline.ipynb`

## 1. Dataset

| dataset_id   |   accounts |   organic |   buzzer |   buzzer_rate |
|:-------------|-----------:|----------:|---------:|--------------:|
| batch2       |         50 |        27 |       23 |         0.460 |
| batch3       |         50 |        21 |       29 |         0.580 |

Total akun berlabel: **100**. Setiap baris mewakili satu akun; `account_group` digunakan untuk group split.

## 2. Feature groups

- **NLP-only:** `avg_tags, avg_body_len, url_rate, avg_words`
- **Temporal-only:** `n_posts, active_hours, post_rate, n_replies, n_quotes, n_originals`
- **Graph-only:** `in_degree, out_degree, total_degree, pagerank, component_size`
- **Combined:** seluruh feature dari tiga kelompok di atas
- `buzzer_score` tidak dimasukkan sebagai fitur dan tidak dianggap sebagai ground truth.

## 3. Group CV result

| model                        | feature_group   |   accuracy |   precision_buzzer |   recall_buzzer |   f1_buzzer |   roc_auc |   pr_auc |   fold_f1_mean |   fold_f1_std |
|:-----------------------------|:----------------|-----------:|-------------------:|----------------:|------------:|----------:|---------:|---------------:|--------------:|
| Majority baseline            | None            |      0.520 |              0.520 |           1.000 |       0.684 |     0.500 |    0.520 |          0.683 |         0.035 |
| NLP-only RF                  | NLP-only        |      0.730 |              0.727 |           0.769 |       0.748 |     0.779 |    0.771 |          0.748 |         0.075 |
| Temporal-only RF             | Temporal-only   |      0.530 |              0.542 |           0.615 |       0.577 |     0.550 |    0.532 |          0.567 |         0.100 |
| Graph-only RF                | Graph-only      |      0.730 |              0.712 |           0.808 |       0.757 |     0.660 |    0.614 |          0.754 |         0.094 |
| Combined Logistic Regression | Combined        |      0.740 |              0.741 |           0.769 |       0.755 |     0.772 |    0.760 |          0.750 |         0.093 |
| Combined RF                  | Combined        |      0.730 |              0.736 |           0.750 |       0.743 |     0.793 |    0.796 |          0.743 |         0.115 |

Group CV menggunakan `StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=42)`. Karena dataset ini satu baris per akun, group split secara matematis mirip account-level stratified CV, tetapi tetap dipakai untuk mencegah pola multi-baris per akun bila dataset bertambah.

## 4. Temporal holdout result

Split temporal: train pada 70 akun paling awal dan test pada 30 akun berikutnya. Batas waktu train: `2026-11-07 03:09:10+00:00`; awal test: `2026-11-07 03:13:24+00:00`.

| model                        | feature_group   |   accuracy |   precision_buzzer |   recall_buzzer |   f1_buzzer |   roc_auc |   pr_auc |
|:-----------------------------|:----------------|-----------:|-------------------:|----------------:|------------:|----------:|---------:|
| NLP-only RF                  | NLP-only        |      0.500 |              0.636 |           0.389 |       0.483 |     0.616 |    0.744 |
| Temporal-only RF             | Temporal-only   |      0.400 |              0.500 |           0.278 |       0.357 |     0.512 |    0.668 |
| Graph-only RF                | Graph-only      |      0.667 |              0.750 |           0.667 |       0.706 |     0.738 |    0.794 |
| Combined Logistic Regression | Combined        |      0.567 |              0.778 |           0.389 |       0.519 |     0.833 |    0.795 |
| Combined RF                  | Combined        |      0.500 |              0.636 |           0.389 |       0.483 |     0.704 |    0.762 |

## 5. Cross-issue result

| train_batch   | test_batch   |   accuracy |   precision_buzzer |   recall_buzzer |   f1_buzzer |   roc_auc |   pr_auc |
|:--------------|:-------------|-----------:|-------------------:|----------------:|------------:|----------:|---------:|
| batch2        | batch3       |      0.420 |              0.500 |           0.138 |       0.216 |     0.531 |    0.609 |
| batch3        | batch2       |      0.420 |              0.200 |           0.087 |       0.121 |     0.609 |    0.491 |

Hasil cross-issue dibaca sebagai uji generalisasi domain, bukan sebagai pengganti evaluasi in-domain.

## 6. Artifacts

- `output/phase5/group_cv_metrics.csv`
- `output/phase5/group_cv_metrics_comparison.png`
- `output/phase5/group_cv_confusion_matrices.png`
- `output/phase5/temporal_metrics.csv`
- `output/phase5/temporal_metrics_comparison.png`
- `output/phase5/temporal_combined_rf_confusion_matrix.png`
- `output/phase5/cross_issue_metrics.csv`
- `output/phase5/cross_issue_metrics_comparison.png`
- `output/phase5/cross_issue_confusion_matrices.png`
- `models/phase5_baseline_rf.pkl`

## 7. Limitations

1. **Selection bias:** label Phase 4 berasal dari Top 30 suspicious + Random 20, bukan sample populasi yang sepenuhnya acak.
2. **Label size:** hanya 100 akun dari dua issue; hasil metrics belum cukup untuk klaim performa produksi.
3. **Annotation quality:** label saat ini single-reviewer/human-in-the-loop dan belum memiliki multi-annotator agreement seperti Cohen's Kappa.
4. **Sparse temporal signal:** banyak akun hanya memiliki satu posting sehingga `active_hours` dan `post_rate` memiliki keterbatasan interpretasi.
5. **Domain shift:** distribusi teks, waktu, dan jaringan Batch 2 vs Batch 3 berbeda.
6. **NLP scope:** NLP-only Phase 5 masih memakai agregat handcrafted, belum IndoBERTweet.
7. **No causal claim:** feature importance atau metrics tidak membuktikan bahwa suatu akun benar-benar buzzer di luar definisi label anotasi.

## 8. Recommendation for Phase 6

Gunakan split dan report Phase 5 sebagai baseline tetap. Phase 6 dapat menambahkan embedding NLP/IndoBERTweet, evaluasi label quality yang lebih kuat, tuning yang nested atau time-aware, dan analisis error pada false positive/false negative tanpa memasukkan `buzzer_score` sebagai label.
