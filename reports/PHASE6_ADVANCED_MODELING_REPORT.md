# CoordinX - Phase 6 Advanced Modeling Report

**Generated (UTC):** 2026-11-10T02:40:41.013780+00:00
**Status:** Prototype selesai; advanced deep-learning branches belum dilatih.
**Model artifact:** `models/phase6_fusion_proxy.pkl`

## 1. Scope

Phase 6 menggunakan data label account-level dari Batch 2 dan Batch 3. Model tidak menggunakan `buzzer_score` sebagai fitur maupun ground truth. Evaluasi utama menggunakan `StratifiedGroupKFold` dan evaluasi lintas isu.

Branch yang dijalankan:

- `text_proxy`: TF-IDF character n-gram sebagai pengganti sementara IndoBERTweet.
- `temporal_proxy`: statistik urutan posting per akun sebagai pengganti sementara LSTM.
- `graph_proxy`: fitur struktur dan agregasi graph sebagai pengganti sementara GraphSAGE.
- `fusion_proxy`: gabungan tiga branch di atas dengan Logistic Regression.

## 2. Group CV Results

| model          |   accuracy |   precision_buzzer |   recall_buzzer |   f1_buzzer |   roc_auc |   pr_auc |   fold_f1_mean |   fold_f1_std |
|:---------------|-----------:|-------------------:|----------------:|------------:|----------:|---------:|---------------:|--------------:|
| text_proxy     |      0.760 |              0.780 |           0.750 |       0.765 |     0.797 |    0.782 |          0.760 |         0.143 |
| temporal_proxy |      0.510 |              0.532 |           0.481 |       0.505 |     0.508 |    0.527 |          0.462 |         0.179 |
| graph_proxy    |      0.630 |              0.714 |           0.481 |       0.575 |     0.645 |    0.621 |          0.566 |         0.119 |
| fusion_proxy   |      0.750 |              0.745 |           0.788 |       0.766 |     0.790 |    0.766 |          0.768 |         0.043 |

## 3. Cross-Issue Results

| branch   | train_batch   | test_batch   |   accuracy |   precision_buzzer |   recall_buzzer |   f1_buzzer |   roc_auc |   pr_auc |
|:---------|:--------------|:-------------|-----------:|-------------------:|----------------:|------------:|----------:|---------:|
| fusion   | batch2        | batch3       |      0.460 |              0.600 |           0.207 |       0.308 |     0.389 |    0.611 |
| fusion   | batch3        | batch2       |      0.680 |              0.706 |           0.522 |       0.600 |     0.651 |    0.658 |

## 4. Data Readiness

- **batch2:** 50 labeled accounts; 40 labeled accounts hanya memiliki satu post; 718 interaction rows; 529 target account IDs tidak dapat dipakai sebagai ID numerik dan diproses melalui fallback username.
- **batch3:** 50 labeled accounts; 40 labeled accounts hanya memiliki satu post; 737 interaction rows; 0 target account IDs tidak dapat dipakai sebagai ID numerik dan diproses melalui fallback username.

Total training rows: **100**. Batch yang sudah digunakan: **batch2, batch3**.

## 5. Explainability and Error Analysis

- `output/phase6/phase6_fusion_explanations.csv` berisi probabilitas, prediksi, dan fitur/term dengan kontribusi terbesar.
- `output/phase6/phase6_error_analysis.csv` berisi false positive dan false negative dari model full-fit.
- `output/phase6/phase6_fusion_confusion_matrix.png` dan `output/phase6/phase6_branch_metrics_comparison.png` berisi visualisasi evaluasi.

## 6. Limitations and Next Gate

- Environment aktif belum memiliki `torch`, `transformers`, atau `torch_geometric`; karena itu artifact ini **bukan** IndoBERTweet, LSTM, atau GraphSAGE.
- Batch 2 dan Batch 3 masing-masing memiliki 40 dari 50 labeled accounts dengan tepat satu post. Data ini terlalu tipis untuk menyimpulkan performa LSTM secara valid.
- Untuk melanjutkan ke deep-learning Phase 6, siapkan environment Python yang memiliki PyTorch, Transformers, dan PyTorch Geometric, lalu tambah label account dengan riwayat multi-post. Jangan menghapus atau menimpa artifact proxy ini.
- Model proxy hanya dipakai sebagai pembanding dan fondasi inference; jangan menyebutnya sebagai model final produksi.

## 7. Artifacts

- `models/phase6_fusion_proxy.pkl`
- `output/phase6/phase6_group_cv_metrics.csv`
- `output/phase6/phase6_group_cv_oof_predictions.csv`
- `output/phase6/phase6_cross_issue_metrics.csv`
- `output/phase6/phase6_fusion_explanations.csv`
- `output/phase6/phase6_error_analysis.csv`
- `output/phase6/phase6_readiness.json`
