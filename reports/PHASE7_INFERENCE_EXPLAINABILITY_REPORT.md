# CoordinX - Phase 7 Inference and Explainability

**Generated (UTC):** 2026-11-10T07:32:08.698275+00:00

## Scope

Inference memakai `phase6_fusion_proxy_combined_canonical.pkl`. Model ini adalah fusion proxy TF-IDF + temporal + graph, bukan IndoBERTweet/LSTM/GraphSAGE final.

## Outputs

- Akun diproses: **1803** ({'batch2': 1007, 'batch3': 796}).
- Prediksi Buzzer: **440**.
- `REVIEW_REQUIRED`: **291**; `PRIORITY_REVIEW`: **328**.
- Rata-rata coordination score: **0.334**.

## Explainability fields

- `coordination_score`, `confidence`, dan `uncertainty` berasal dari probabilitas model.
- `text_evidence` menunjukkan akun dengan teks paling mirip di issue yang sama.
- `temporal_evidence` merangkum jumlah post, active span, post rate, dan burst ratio.
- `graph_evidence` merangkum in-degree, out-degree, total-degree, dan component size.
- `positive_model_evidence` dan `negative_model_evidence` menunjukkan kontribusi fitur/term linear terbesar.
- `human_evidence` dan `human_label` dipertahankan hanya sebagai metadata anotasi; prediksi tidak mengubah label manual.

## Human review

`REVIEW_REQUIRED` dipakai untuk probabilitas 0.35-0.65. `PRIORITY_REVIEW` dipakai untuk prediksi Buzzer di luar rentang tersebut. Status ini adalah prioritas kerja, bukan ground truth.

## Artifacts

- `data/predictions/phase7_combined_predictions.csv`
- `data/predictions/phase7_batch2_predictions.csv`
- `data/predictions/phase7_batch3_predictions.csv`
- `output/phase7/phase7_predictions.csv`
- `output/phase7/phase7_priority_review.csv`
- `output/phase7/phase7_coordination_score_distribution.png`
- `output/phase7/phase7_readiness.json`