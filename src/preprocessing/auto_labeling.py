#!/usr/bin/env python3
"""Generate explicit pseudo-labels for new canonical account features."""
from __future__ import annotations

import argparse
import json
import pickle
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from models.phase6_advanced import MODEL_FEATURES, find_repo_root


def _prepare_frame(frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame.copy()
    frame["text_blob"] = frame.get("text_blob", "").fillna("").astype(str)
    for column in MODEL_FEATURES:
        if column not in frame.columns:
            frame[column] = np.nan
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    return frame


def generate_pseudo_labels(
    root: str | Path | None,
    batch: str,
    high_threshold: float = 0.65,
    low_threshold: float = 0.35,
) -> dict[str, Any]:
    root_path = find_repo_root(root)
    features_path = root_path / "data" / "features" / f"{batch}_account_features_with_scores.csv"
    model_path = root_path / "models" / "phase6_fusion_proxy_combined_canonical.pkl"
    if not features_path.exists():
        raise FileNotFoundError(f"Canonical feature file tidak ditemukan: {features_path}")
    if not model_path.exists():
        raise FileNotFoundError(f"Model proxy tidak ditemukan: {model_path}")

    frame = _prepare_frame(pd.read_csv(features_path, dtype="string", keep_default_na=True))
    with model_path.open("rb") as handle:
        artifact = pickle.load(handle)
    model = artifact["model"]
    probabilities = model.predict_proba(frame)[:, 1]
    pseudo_label = (probabilities >= 0.5).astype(int)
    confidence = np.maximum(probabilities, 1.0 - probabilities)
    label_class = np.select(
        [probabilities >= high_threshold, probabilities <= low_threshold],
        ["Buzzer", "Organic"],
        default="Unknown",
    )
    review_status = np.where(
        label_class == "Unknown",
        "AUTO_UNKNOWN_REVIEW",
        "AUTO_PSEUDO_LABEL_UNVERIFIED",
    )

    output = frame[["account_id", "username", "dataset_id", "issue_id"]].copy()
    output["label"] = pd.Series(pseudo_label, index=output.index, dtype="Int64")
    output["pseudo_label"] = pseudo_label
    output["pseudo_label_name"] = np.where(pseudo_label == 1, "Buzzer", "Organic")
    output["label_class"] = label_class
    output.loc[output["label_class"].eq("Unknown"), "label"] = pd.NA
    output["model_probability_buzzer"] = probabilities
    output["confidence"] = confidence
    output["buzzer_score_heuristic"] = pd.to_numeric(frame.get("buzzer_score"), errors="coerce")
    output["evidence"] = frame.apply(
        lambda row: (
            f"proxy_probability={float(probabilities[row.name]):.4f}; "
            f"heuristic_buzzer_score={float(pd.to_numeric(pd.Series([row.get('buzzer_score')]), errors='coerce').fillna(0).iloc[0]):.4f}; "
            f"posts={row.get('n_posts', 0)}; post_rate={row.get('post_rate', 0)}; "
            f"out_degree={row.get('out_degree', 0)}; total_degree={row.get('total_degree', 0)}"
        ), axis=1,
    )
    output["notes"] = (
        "Pseudo-label otomatis dari model proxy combined; bukan ground truth manual. "
        "Unknown perlu review sebelum dipakai untuk training final."
    )
    output["review_status"] = review_status
    output["candidate_type"] = np.where(label_class == "Unknown", "AUTO_UNKNOWN", "AUTO_PROXY_PREDICTION")
    output["label_source"] = "phase6_fusion_proxy_combined_canonical"
    output["model_version"] = f"{model_path.name}:{artifact.get('created_at_utc', 'unknown')}"
    output["schema_version"] = "pseudo-label-v1"

    labels_dir = root_path / "data" / "labels"
    labels_dir.mkdir(parents=True, exist_ok=True)
    output_path = labels_dir / f"{batch}_auto_pseudo_labels.csv"
    output.to_csv(output_path, index=False, encoding="utf-8-sig")

    summary = {
        "status": "AUTO_PSEUDO_LABELS_ONLY",
        "batch": batch,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_features": str(features_path),
        "source_model": str(model_path),
        "rows": int(len(output)),
        "pseudo_label_counts": {str(key): int(value) for key, value in output["pseudo_label"].value_counts().sort_index().items()},
        "label_class_counts": {str(key): int(value) for key, value in output["label_class"].value_counts().sort_index().items()},
        "review_status_counts": {str(key): int(value) for key, value in output["review_status"].value_counts().sort_index().items()},
        "thresholds": {"organic_max_probability": low_threshold, "buzzer_min_probability": high_threshold},
        "artifacts": {"pseudo_labels": str(output_path)},
        "warning": "Pseudo-labels are model outputs and must not replace human ground truth.",
    }
    summary_path = labels_dir / f"{batch}_auto_pseudo_labels.json"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    summary["artifacts"]["summary"] = str(summary_path)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate explicit automatic pseudo-labels")
    parser.add_argument("--root", default=None)
    parser.add_argument("--batch", required=True)
    parser.add_argument("--high-threshold", type=float, default=0.65)
    parser.add_argument("--low-threshold", type=float, default=0.35)
    args = parser.parse_args()
    result = generate_pseudo_labels(**vars(args))
    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
