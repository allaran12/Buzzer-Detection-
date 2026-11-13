# Repository Audit

## Scope

This audit follows the CoordinX PRD and covers the existing Python pipeline, model artifacts, datasets, tests, and web integration before model deployment changes.

## Current Structure

- `src/preprocessing/`: ingestion, cleaning, standardization, and labeling helpers.
- `src/features/`: canonical feature generation.
- `src/models/`: Phase 6 proxy/fusion training code.
- `src/inference/`: Phase 7 offline inference and explainability.
- `models/`: serialized model artifacts, including `phase6_fusion_proxy_batch2_canonical.pkl`.
- `data/`: processed data, feature metadata, labels, and predictions.
- `web/`: Next.js frontend and API proxy routes.
- `tests/`: Python validation, canonical pipeline, and Phase 6 tests.

## Existing Implementation

The requested artifact is `models/phase6_fusion_proxy_batch2_canonical.pkl`. Its training implementation is in `src/models/phase6_advanced.py` and `src/models/canonical_retraining.py`. The artifact is a fusion proxy using character TF-IDF text features and numeric temporal/account/graph features with a scikit-learn classifier. It is not an IndoBERTweet, LSTM, or GraphSAGE production model.

Offline inference is implemented by `src/inference/phase7_inference.py`. It expects canonical account feature CSV files rather than a raw X URL and emits account-level predictions, probabilities, uncertainty, evidence fields, and review status.

The web application currently has a Next.js `/api/analyze` route with an optional external FastAPI proxy and a simulation fallback. The frontend still hardcodes several analysis summary values. No FastAPI application currently exists in this repository.

## Working Components

- Canonical feature and Phase 6 training artifacts exist.
- Offline inference code and explainability output exist.
- Existing preprocessing and data validation modules exist.
- Next.js frontend and proxy route run independently.
- Model artifact is present at the requested path.

## Broken or Incomplete Components

- The pickle cannot currently be loaded in the default environment because its custom transformer requires `models.phase6_advanced` and that module imports optional dependencies such as matplotlib.
- There is no HTTP inference service for the pickle.
- The frontend request contains a URL, while the model requires canonical account-level features.
- The frontend uses hardcoded score, risk, phrase, and sentiment values instead of model response fields.
- Dashboard account data remains mock data.
- The current proxy fallback can silently return synthetic results when a backend fails.

## Data Quality and Modeling Concerns

- Batch2 training labels cover only a small subset of accounts.
- The model is an experimental proxy and must expose model version and review status.
- Batch2-to-batch3 generalization is materially weaker than internal batch2 evaluation according to the existing comparison report.
- Missing feature columns are currently imputed, which can hide schema mismatch unless the service validates input explicitly.
- Pickle loading is version and module-path dependent.
- URL collection, raw post retrieval, temporal features, and graph construction are not yet part of the web request path.

## Missing Tests

- Configurable model registry and model switching.
- Artifact load and module/dependency diagnostics.
- Strict canonical feature validation.
- HTTP health/model metadata/inference contracts.
- Mapping model output into the frontend account schema.
- Explicit distinction between model, simulation, and error sources.
- End-to-end request using a real canonical feature CSV.

## Recommended Next Steps

1. Add a configurable model registry and adapter so batch2, batch3, and combined artifacts share one interface.
2. Add explicit feature contracts and validation before inference.
3. Add a FastAPI service that loads one configured model at startup and exposes health, metadata, and inference endpoints.
4. Update the Next.js proxy and Hero UI to consume real response values.
5. Replace mock account responses only after the model-backed response contract is stable.
6. Integrate URL collection and request-time feature generation as a separate phase; do not fabricate model features from a URL.
7. Keep the experimental status, model metadata, uncertainty, and human-review requirement visible in API responses.

## PRD Mapping

- Data validation/preprocessing: partially implemented offline.
- Feature engineering: implemented for canonical batch artifacts.
- Model inference: implemented offline only.
- Evidence and human review: partially implemented in Phase 7 output.
- Dashboard: implemented as a demo frontend, not model-backed.
- Reproducibility and model switching: requires the planned registry/configuration layer.
- URL-to-feature workflow: not implemented and must remain a separate integration phase.

## Phase 0 Verification Note

The artifact file exists, but loading it in the current environment failed before deserialization completed because the environment is missing `matplotlib`. The next phase must provide a clear dependency check and actionable startup error rather than silently falling back to simulation.
