#!/usr/bin/env python3
"""Phase 7 inference and explainability for canonical CoordinX features."""
from __future__ import annotations

import argparse
import json
import pickle
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors

from models.phase6_advanced import MODEL_FEATURES, find_repo_root


BATCHES = ("batch2", "batch3")


def _read_features(root: Path, batch: str) -> pd.DataFrame:
    path = root / "data" / "features" / f"{batch}_account_features_with_scores.csv"
    if not path.exists():
        raise FileNotFoundError(f"Canonical feature file tidak ditemukan: {path}")
    frame = pd.read_csv(path, dtype="string", keep_default_na=True)
    frame["dataset_id"] = batch
    frame["issue_id"] = frame.get("issue_id", "wowo2" if batch == "batch2" else "RoySuryo").fillna(
        "wowo2" if batch == "batch2" else "RoySuryo"
    )
    frame["text_blob"] = frame.get("text_blob", "").fillna("").astype(str)
    for column in MODEL_FEATURES:
        if column not in frame.columns:
            frame[column] = np.nan
        else:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
    return frame


def _text_similarity(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame[["account_id", "dataset_id"]].copy()
    result["text_similarity_score"] = 0.0
    result["text_similarity_account_id"] = pd.NA
    result["text_similarity_username"] = pd.NA
    for dataset_id, indices in frame.groupby("dataset_id").groups.items():
        positions = list(indices)
        if len(positions) < 2:
            continue
        texts = frame.loc[positions, "text_blob"].fillna("").astype(str).tolist()
        if not any(text.strip() for text in texts):
            continue
        vectorizer = TfidfVectorizer(
            analyzer="char",
            ngram_range=(3, 5),
            min_df=1,
            max_features=3000,
            sublinear_tf=True,
        )
        matrix = vectorizer.fit_transform(texts)
        neighbors = NearestNeighbors(n_neighbors=2, metric="cosine", algorithm="brute").fit(matrix)
        distances, neighbor_positions = neighbors.kneighbors(matrix)
        for local_position, global_index in enumerate(positions):
            neighbor_local = int(neighbor_positions[local_position, 1])
            neighbor_index = positions[neighbor_local]
            result.loc[global_index, "text_similarity_score"] = float(1 - distances[local_position, 1])
            result.loc[global_index, "text_similarity_account_id"] = frame.loc[neighbor_index, "account_id"]
            result.loc[global_index, "text_similarity_username"] = frame.loc[neighbor_index, "username"]
    return result


def _linear_evidence(model, frame: pd.DataFrame) -> pd.DataFrame:
    transformed = model.named_steps["preprocess"].transform(frame)
    coefficients = model.named_steps["model"].coef_[0]
    names = model.named_steps["preprocess"].get_feature_names_out()
    rows = []
    for position in range(len(frame)):
        values = transformed[position].toarray().ravel() if hasattr(transformed[position], "toarray") else np.asarray(transformed[position]).ravel()
        contributions = values * coefficients
        positive_indices = np.argsort(contributions)[::-1]
        negative_indices = np.argsort(contributions)
        positive = [
            f"{names[index]} ({contributions[index]:+.3f})"
            for index in positive_indices if contributions[index] > 0
        ][:5]
        negative = [
            f"{names[index]} ({contributions[index]:+.3f})"
            for index in negative_indices if contributions[index] < 0
        ][:5]
        rows.append({
            "positive_model_evidence": "; ".join(positive),
            "negative_model_evidence": "; ".join(negative),
        })
    return pd.DataFrame(rows)


def _format_number(value: Any, digits: int = 2) -> str:
    number = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    return "n/a" if pd.isna(number) else f"{float(number):.{digits}f}"


def run_inference(root: str | Path | None = None, experiment: str = "combined") -> dict[str, Any]:
    root_path = find_repo_root(root)
    model_path = root_path / "models" / f"phase6_fusion_proxy_{experiment}_canonical.pkl"
    if not model_path.exists():
        raise FileNotFoundError(f"Model canonical tidak ditemukan: {model_path}")
    with model_path.open("rb") as handle:
        artifact = pickle.load(handle)
    model = artifact["model"]

    frame = pd.concat([_read_features(root_path, batch) for batch in BATCHES], ignore_index=True)
    predictions = model.predict(frame).astype(int)
    probabilities = model.predict_proba(frame)[:, 1]
    frame["human_label"] = frame.get("label")
    frame["human_evidence"] = frame.get("evidence")
    frame["human_review_status"] = frame.get("review_status")
    frame["human_candidate_type"] = frame.get("candidate_type")

    output = frame[[
        "account_id", "username", "dataset_id", "issue_id", "human_label",
        "human_evidence", "human_review_status", "human_candidate_type",
    ]].copy()
    output["prediction"] = np.where(predictions == 1, "Buzzer", "Organic")
    output["prediction_binary"] = predictions
    output["probability_buzzer"] = probabilities
    output["coordination_score"] = probabilities
    output["confidence"] = np.maximum(probabilities, 1 - probabilities)
    output["uncertainty"] = 1 - output["confidence"]
    output["score_band"] = pd.cut(
        output["coordination_score"],
        bins=[-np.inf, 0.35, 0.65, np.inf],
        labels=["low", "review", "high"],
    ).astype(str)

    similarity = _text_similarity(frame)
    output = output.merge(similarity, on=["account_id", "dataset_id"], how="left")
    evidence = _linear_evidence(model, frame)
    output = pd.concat([output.reset_index(drop=True), evidence], axis=1)

    output["temporal_evidence"] = frame.apply(
        lambda row: (
            f"{_format_number(row.get('n_posts'), 0)} posts; "
            f"active span {_format_number(row.get('active_hours'), 2)}h; "
            f"post rate {_format_number(row.get('post_rate'), 2)}/h; "
            f"burst <=1h {_format_number(row.get('burst_ratio_1h'), 2)}"
        ), axis=1,
    )
    output["graph_evidence"] = frame.apply(
        lambda row: (
            f"in={_format_number(row.get('in_degree'), 0)}, "
            f"out={_format_number(row.get('out_degree'), 0)}, "
            f"total={_format_number(row.get('total_degree'), 0)}, "
            f"component={_format_number(row.get('component_size'), 0)}"
        ), axis=1,
    )
    output["text_evidence"] = output.apply(
        lambda row: (
            f"nearest={row['text_similarity_username']} "
            f"similarity={_format_number(row['text_similarity_score'], 3)}"
            if pd.notna(row["text_similarity_username"])
            else "no comparable text"
        ), axis=1,
    )
    output["review_status"] = np.select(
        [output["uncertainty"] >= 0.35, output["prediction_binary"] == 1],
        ["REVIEW_REQUIRED", "PRIORITY_REVIEW"],
        default="LOW_PRIORITY",
    )
    output["model_version"] = f"{model_path.name}:{artifact.get('created_at_utc', 'unknown')}"
    output["schema_version"] = artifact.get("schema_version", "canonical-v1")

    predictions_dir = root_path / "data" / "predictions"
    output_dir = root_path / "output" / "phase7"
    predictions_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    combined_path = predictions_dir / "phase7_combined_predictions.csv"
    output_path = output_dir / "phase7_predictions.csv"
    review_path = output_dir / "phase7_priority_review.csv"
    output.to_csv(combined_path, index=False, encoding="utf-8-sig")
    output.to_csv(output_path, index=False, encoding="utf-8-sig")
    output[output["review_status"].isin(["REVIEW_REQUIRED", "PRIORITY_REVIEW"])].sort_values(
        ["review_status", "coordination_score"], ascending=[True, False]
    ).to_csv(review_path, index=False, encoding="utf-8-sig")
    for batch in BATCHES:
        output[output["dataset_id"] == batch].to_csv(
            predictions_dir / f"phase7_{batch}_predictions.csv", index=False, encoding="utf-8-sig"
        )

    fig, axis = plt.subplots(figsize=(8, 5))
    for batch, group in output.groupby("dataset_id"):
        axis.hist(group["coordination_score"], bins=20, alpha=0.55, label=batch)
    axis.set_title("Phase 7 Coordination Score Distribution")
    axis.set_xlabel("Coordination score (model probability)")
    axis.set_ylabel("Accounts")
    axis.legend()
    fig.tight_layout()
    figure_path = output_dir / "phase7_coordination_score_distribution.png"
    fig.savefig(figure_path, dpi=180)
    plt.close(fig)

    readiness = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "model_path": str(model_path),
        "model_version": output["model_version"].iloc[0],
        "schema_version": output["schema_version"].iloc[0],
        "rows": int(len(output)),
        "batches": {batch: int((output["dataset_id"] == batch).sum()) for batch in BATCHES},
        "predicted_buzzer": int((output["prediction_binary"] == 1).sum()),
        "review_required": int((output["review_status"] == "REVIEW_REQUIRED").sum()),
        "priority_review": int((output["review_status"] == "PRIORITY_REVIEW").sum()),
        "mean_coordination_score": float(output["coordination_score"].mean()),
        "artifacts": {
            "combined_predictions": str(combined_path),
            "predictions_report": str(output_path),
            "priority_review": str(review_path),
            "score_distribution": str(figure_path),
        },
    }
    readiness_path = output_dir / "phase7_readiness.json"
    readiness_path.write_text(json.dumps(readiness, indent=2, default=str), encoding="utf-8")

    report_path = root_path / "reports" / "PHASE7_INFERENCE_EXPLAINABILITY_REPORT.md"
    report_path.write_text(
        "\n".join([
            "# CoordinX - Phase 7 Inference and Explainability",
            "",
            f"**Generated (UTC):** {readiness['generated_at_utc']}",
            "",
            "## Scope",
            "",
            "Inference memakai `phase6_fusion_proxy_combined_canonical.pkl`. Model ini adalah fusion proxy TF-IDF + temporal + graph, bukan IndoBERTweet/LSTM/GraphSAGE final.",
            "",
            "## Outputs",
            "",
            f"- Akun diproses: **{readiness['rows']}** ({readiness['batches']}).",
            f"- Prediksi Buzzer: **{readiness['predicted_buzzer']}**.",
            f"- `REVIEW_REQUIRED`: **{readiness['review_required']}**; `PRIORITY_REVIEW`: **{readiness['priority_review']}**.",
            f"- Rata-rata coordination score: **{readiness['mean_coordination_score']:.3f}**.",
            "",
            "## Explainability fields",
            "",
            "- `coordination_score`, `confidence`, dan `uncertainty` berasal dari probabilitas model.",
            "- `text_evidence` menunjukkan akun dengan teks paling mirip di issue yang sama.",
            "- `temporal_evidence` merangkum jumlah post, active span, post rate, dan burst ratio.",
            "- `graph_evidence` merangkum in-degree, out-degree, total-degree, dan component size.",
            "- `positive_model_evidence` dan `negative_model_evidence` menunjukkan kontribusi fitur/term linear terbesar.",
            "- `human_evidence` dan `human_label` dipertahankan hanya sebagai metadata anotasi; prediksi tidak mengubah label manual.",
            "",
            "## Human review",
            "",
            "`REVIEW_REQUIRED` dipakai untuk probabilitas 0.35-0.65. `PRIORITY_REVIEW` dipakai untuk prediksi Buzzer di luar rentang tersebut. Status ini adalah prioritas kerja, bukan ground truth.",
            "",
            "## Artifacts",
            "",
            "- `data/predictions/phase7_combined_predictions.csv`",
            "- `data/predictions/phase7_batch2_predictions.csv`",
            "- `data/predictions/phase7_batch3_predictions.csv`",
            "- `output/phase7/phase7_predictions.csv`",
            "- `output/phase7/phase7_priority_review.csv`",
            "- `output/phase7/phase7_coordination_score_distribution.png`",
            "- `output/phase7/phase7_readiness.json`",
        ]),
        encoding="utf-8",
    )
    return {"predictions": output, "readiness": readiness, "report_path": report_path}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run CoordinX Phase 7 inference")
    parser.add_argument("--root", default=None)
    parser.add_argument("--experiment", default="combined")
    args = parser.parse_args()
    result = run_inference(args.root, args.experiment)
    print(json.dumps(result["readiness"], indent=2, default=str))
