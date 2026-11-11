# CoordinX - Canonical Model Comparison

**Generated (UTC):** 2026-11-10T05:51:23.525466+00:00

## 1. Canonical data validation

- `batch2`: 1514 posts, 1007 accounts, 651 valid edge events, 642 unique directed edges.
- Labels: {'0': 27, '1': 23}; unmatched labels: 0.
- `batch3`: 1081 posts, 796 accounts, 714 valid edge events, 695 unique directed edges.
- Labels: {'0': 21, '1': 29}; unmatched labels: 0.

## 2. Group CV comparison

| source                                 |   accuracy |   precision_buzzer |   recall_buzzer |   f1_buzzer |   roc_auc |   pr_auc |
|:---------------------------------------|-----------:|-------------------:|----------------:|------------:|----------:|---------:|
| Phase 5 Combined RF                    |       0.73 |              0.736 |           0.75  |       0.743 |     0.793 |    0.796 |
| Phase 5 Combined Logistic Regression   |       0.74 |              0.741 |           0.769 |       0.755 |     0.772 |    0.76  |
| Phase 6 fusion proxy (legacy features) |       0.75 |              0.745 |           0.788 |       0.766 |     0.79  |    0.766 |
| Phase 6 canonical batch2               |       0.88 |              0.87  |           0.87  |       0.87  |     0.88  |    0.791 |
| Phase 6 canonical batch3               |       0.64 |              0.69  |           0.69  |       0.69  |     0.609 |    0.714 |
| Phase 6 canonical combined             |       0.75 |              0.729 |           0.827 |       0.775 |     0.808 |    0.776 |

## 3. Cross-issue evaluation

Cross-issue scores are reported only for the combined canonical experiment because batch-only models do not contain the other issue in their training artifact.

| train_batch   | test_batch   |   accuracy |   precision_buzzer |   recall_buzzer |   f1_buzzer |   roc_auc |   pr_auc |
|:--------------|:-------------|-----------:|-------------------:|----------------:|------------:|----------:|---------:|
| batch2        | batch3       |       0.44 |              0.538 |           0.241 |       0.333 |     0.389 |    0.564 |
| batch3        | batch2       |       0.7  |              0.7   |           0.609 |       0.651 |     0.749 |    0.707 |

## 4. Interpretation

- Canonical features are regenerated from standardized data and use string-preserved IDs.
- `buzzer_score` remains a heuristic review aid and is excluded from model features and ground truth.
- All evaluations are account-level; no post-level random split is used.
- The Phase 6 artifacts remain TF-IDF/temporal/graph proxy models because the active environment lacks the deep-learning backends.
- Metrics are descriptive only: each batch has 50 manually labeled accounts and many accounts have one post.

## 5. Artifacts

- `data/features/batch2_*` and `data/features/batch3_*` canonical feature files
- `data/labels/batch2_labeled_canonical.csv` and `data/labels/batch3_labeled_canonical.csv`
- `models/phase6_fusion_proxy_batch2_canonical.pkl`
- `models/phase6_fusion_proxy_batch3_canonical.pkl`
- `models/phase6_fusion_proxy_combined_canonical.pkl`
- `output/phase6_canonical/` per-experiment metrics, matrices, explanations, and readiness files