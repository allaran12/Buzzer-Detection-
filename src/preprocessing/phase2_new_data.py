#!/usr/bin/env python3
"""Prepare the new raw datasets through ingestion, EDA, features, and pseudo-labeling."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors

from features.canonical_features import generate_batch, repo_root
from preprocessing.auto_labeling import generate_pseudo_labels
from preprocessing.ingest import run_ingest


NEW_DATASETS = {
    "batch4": {"raw": "data/raw/ManfaatnyaDirasakan.csv", "issue_id": "ManfaatnyaDirasakan"},
    "batch5": {"raw": "data/raw/rasanyaman.csv", "issue_id": "rasanyaman"},
    "batch6": {"raw": "data/raw/misi18tokped.csv", "issue_id": "misi18tokped"},
}


def _read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype="string", keep_default_na=True)


def _audit_overlap(root: Path, batches: tuple[str, ...]) -> list[dict[str, Any]]:
    frames = {
        batch: _read_csv(root / "data" / "processed" / NEW_DATASETS[batch]["issue_id"] / "standardized_data.csv")
        for batch in batches
    }
    rows: list[dict[str, Any]] = []
    for left_position, left_batch in enumerate(batches):
        for right_batch in batches[left_position + 1:]:
            left_posts = set(frames[left_batch]["post_id"].dropna().astype(str))
            right_posts = set(frames[right_batch]["post_id"].dropna().astype(str))
            left_accounts = set(frames[left_batch]["account_id"].dropna().astype(str))
            right_accounts = set(frames[right_batch]["account_id"].dropna().astype(str))
            post_overlap = left_posts & right_posts
            account_overlap = left_accounts & right_accounts
            smaller_post_set = max(1, min(len(left_posts), len(right_posts)))
            rows.append({
                "left_batch": left_batch,
                "right_batch": right_batch,
                "left_issue": NEW_DATASETS[left_batch]["issue_id"],
                "right_issue": NEW_DATASETS[right_batch]["issue_id"],
                "left_posts": len(left_posts),
                "right_posts": len(right_posts),
                "overlapping_post_ids": len(post_overlap),
                "post_overlap_ratio_of_smaller": round(len(post_overlap) / smaller_post_set, 6),
                "overlapping_account_ids": len(account_overlap),
                "near_duplicate": len(post_overlap) / smaller_post_set >= 0.95,
            })
    return rows


def _write_eda(root: Path, summaries: list[dict[str, Any]], batches: tuple[str, ...]) -> dict[str, str]:
    output_dir = root / "output" / "phase2_new_data"
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_frame = pd.DataFrame(summaries)
    summary_path = output_dir / "dataset_summary.csv"
    summary_frame.to_csv(summary_path, index=False, encoding="utf-8-sig")

    figure, axis = plt.subplots(figsize=(9, 5))
    summary_frame.set_index("batch")[["cleaned_posts", "accounts"]].plot(kind="bar", ax=axis)
    axis.set_title("Phase 2 New Data - Posts and Accounts")
    axis.set_ylabel("Count")
    axis.set_xlabel("Dataset")
    axis.tick_params(axis="x", rotation=0)
    figure.tight_layout()
    counts_path = output_dir / "posts_accounts_distribution.png"
    figure.savefig(counts_path, dpi=180)
    plt.close(figure)

    relation_rows: list[dict[str, Any]] = []
    hourly_rows: list[dict[str, Any]] = []
    for batch in batches:
        path = root / "data" / "processed" / NEW_DATASETS[batch]["issue_id"] / "standardized_data.csv"
        frame = _read_csv(path)
        relation = frame["relation_type"].fillna("unknown").value_counts()
        relation_rows.extend(
            {"batch": batch, "relation_type": str(key), "posts": int(value)}
            for key, value in relation.items()
        )
        dates = pd.to_datetime(frame["date"], errors="coerce", utc=True)
        hourly = dates.dt.hour.value_counts().sort_index()
        hourly_rows.extend(
            {"batch": batch, "hour_utc": int(key), "posts": int(value)}
            for key, value in hourly.items()
        )
    relation_frame = pd.DataFrame(relation_rows)
    relation_path = output_dir / "relation_distribution.csv"
    relation_frame.to_csv(relation_path, index=False, encoding="utf-8-sig")
    figure, axis = plt.subplots(figsize=(9, 5))
    relation_frame.pivot(index="relation_type", columns="batch", values="posts").fillna(0).plot(kind="bar", ax=axis)
    axis.set_title("Phase 2 New Data - Interaction Types")
    axis.set_ylabel("Posts")
    axis.set_xlabel("Relation type")
    axis.tick_params(axis="x", rotation=0)
    figure.tight_layout()
    relation_figure = output_dir / "relation_distribution.png"
    figure.savefig(relation_figure, dpi=180)
    plt.close(figure)

    hourly_frame = pd.DataFrame(hourly_rows)
    hourly_path = output_dir / "hourly_activity.csv"
    hourly_frame.to_csv(hourly_path, index=False, encoding="utf-8-sig")
    figure, axis = plt.subplots(figsize=(10, 5))
    for batch, group in hourly_frame.groupby("batch"):
        axis.plot(group["hour_utc"], group["posts"], marker="o", label=batch)
    axis.set_title("Phase 2 New Data - Hourly Activity (UTC)")
    axis.set_xlabel("Hour UTC")
    axis.set_ylabel("Posts")
    axis.set_xticks(range(0, 24, 2))
    axis.legend()
    figure.tight_layout()
    hourly_figure = output_dir / "hourly_activity.png"
    figure.savefig(hourly_figure, dpi=180)
    plt.close(figure)

    hashtag_rows: list[dict[str, Any]] = []
    for batch in batches:
        path = root / "data" / "processed" / NEW_DATASETS[batch]["issue_id"] / "standardized_data.csv"
        frame = _read_csv(path)
        hashtags = frame["text"].fillna("").str.findall(r"#[\w_]+", flags=0).explode().dropna()
        for hashtag, count in hashtags.value_counts().head(15).items():
            hashtag_rows.append({"batch": batch, "hashtag": hashtag, "posts": int(count)})
    hashtag_frame = pd.DataFrame(hashtag_rows)
    hashtag_path = output_dir / "top_hashtags.csv"
    hashtag_frame.to_csv(hashtag_path, index=False, encoding="utf-8-sig")
    figure, axis = plt.subplots(figsize=(11, 6))
    if not hashtag_frame.empty:
        plot_frame = hashtag_frame.sort_values(["batch", "posts"], ascending=[True, False]).copy()
        plot_frame["label"] = plot_frame["batch"] + ":" + plot_frame["hashtag"]
        axis.barh(plot_frame["label"], plot_frame["posts"])
        axis.invert_yaxis()
    axis.set_title("Phase 2 New Data - Top Hashtags")
    axis.set_xlabel("Posts")
    figure.tight_layout()
    hashtag_figure = output_dir / "top_hashtags.png"
    figure.savefig(hashtag_figure, dpi=180)
    plt.close(figure)

    similarity_rows: list[dict[str, Any]] = []
    for batch in batches:
        path = root / "data" / "features" / f"{batch}_account_features.csv"
        frame = _read_csv(path)
        texts = frame["text_blob"].fillna("").astype(str).tolist()
        if len(texts) < 2 or not any(text.strip() for text in texts):
            mean_similarity = 0.0
            max_similarity = 0.0
        else:
            matrix = TfidfVectorizer(analyzer="char", ngram_range=(3, 5), min_df=1, max_features=3000).fit_transform(texts)
            neighbors = NearestNeighbors(n_neighbors=2, metric="cosine", algorithm="brute").fit(matrix)
            distances, _ = neighbors.kneighbors(matrix)
            similarities = 1.0 - distances[:, 1]
            mean_similarity = float(similarities.mean())
            max_similarity = float(similarities.max())
        similarity_rows.append({
            "batch": batch,
            "accounts": len(texts),
            "mean_nearest_text_similarity": round(mean_similarity, 6),
            "max_nearest_text_similarity": round(max_similarity, 6),
        })
    similarity_frame = pd.DataFrame(similarity_rows)
    similarity_path = output_dir / "text_similarity_summary.csv"
    similarity_frame.to_csv(similarity_path, index=False, encoding="utf-8-sig")
    figure, axis = plt.subplots(figsize=(8, 5))
    axis.bar(similarity_frame["batch"], similarity_frame["mean_nearest_text_similarity"])
    axis.set_title("Phase 2 New Data - Mean Nearest Text Similarity")
    axis.set_ylabel("Cosine similarity")
    axis.set_ylim(0, 1)
    figure.tight_layout()
    similarity_figure = output_dir / "text_similarity_summary.png"
    figure.savefig(similarity_figure, dpi=180)
    plt.close(figure)

    return {
        "summary": str(summary_path),
        "posts_accounts_figure": str(counts_path),
        "relation_csv": str(relation_path),
        "relation_figure": str(relation_figure),
        "hourly_csv": str(hourly_path),
        "hourly_figure": str(hourly_figure),
        "hashtags_csv": str(hashtag_path),
        "hashtags_figure": str(hashtag_figure),
        "text_similarity_csv": str(similarity_path),
        "text_similarity_figure": str(similarity_figure),
    }


def run_phase2_new_data(root: str | Path | None = None) -> dict[str, Any]:
    root_path = repo_root(root)
    batches = tuple(NEW_DATASETS)
    ingestion: dict[str, Any] = {}
    feature_validation: dict[str, Any] = {}
    pseudo_labeling: dict[str, Any] = {}
    summaries: list[dict[str, Any]] = []

    for batch, config in NEW_DATASETS.items():
        raw_path = root_path / config["raw"]
        run_ingest(str(raw_path), str(root_path / "data" / "interim"), str(root_path / "data" / "processed"))
        clean_report_path = root_path / "data" / "interim" / config["issue_id"] / f"{config['issue_id']}_report.txt"
        standardized_path = root_path / "data" / "processed" / config["issue_id"] / "standardized_data.csv"
        standardized = _read_csv(standardized_path)
        ingestion[batch] = {
            "batch": batch,
            "issue_id": config["issue_id"],
            "raw": str(raw_path),
            "clean_report": str(clean_report_path),
            "standardized": str(standardized_path),
            "raw_rows": int(len(_read_csv(raw_path))),
            "cleaned_posts": int(len(standardized)),
            "accounts": int(standardized["account_id"].nunique(dropna=True)),
            "duplicate_post_ids": int(standardized["post_id"].duplicated().sum()),
            "missing_required_values": int(standardized[["post_id", "account_id", "username", "text", "date"]].isna().any(axis=1).sum()),
        }
        summaries.append(ingestion[batch])

    overlap = _audit_overlap(root_path, batches)
    overlap_frame = pd.DataFrame(overlap)
    overlap_dir = root_path / "output" / "phase2_new_data"
    overlap_dir.mkdir(parents=True, exist_ok=True)
    overlap_path = overlap_dir / "cross_dataset_overlap.csv"
    overlap_frame.to_csv(overlap_path, index=False, encoding="utf-8-sig")

    for batch in batches:
        feature_validation[batch] = generate_batch(root_path, batch)
        pseudo_labeling[batch] = generate_pseudo_labels(root_path, batch)

    eda_artifacts = _write_eda(root_path, summaries, batches)
    duplicate_batches = [
        row["right_batch"]
        for row in overlap
        if row["near_duplicate"] and row["left_batch"] == "batch4"
    ]
    readiness = {
        "status": "READY_FOR_PROTOTYPE_WITH_PSEUDO_LABEL_WARNING",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "batches": list(batches),
        "ingestion": ingestion,
        "cross_dataset_overlap": overlap,
        "excluded_from_independent_comparison": duplicate_batches,
        "feature_validation": feature_validation,
        "pseudo_labeling": pseudo_labeling,
        "eda_artifacts": eda_artifacts,
        "label_policy": {
            "manual_ground_truth_changed": False,
            "pseudo_labels_are_training_ready_only_for_experiment": True,
            "unknown_requires_review": True,
            "source_model": "phase6_fusion_proxy_combined_canonical.pkl",
        },
        "artifacts": {"overlap": str(overlap_path)},
    }
    readiness_path = overlap_dir / "phase2_readiness.json"
    readiness_path.write_text(json.dumps(readiness, indent=2, ensure_ascii=False, default=str), encoding="utf-8")

    report_lines = [
        "# Phase 2 - New Data Readiness and EDA",
        "",
        f"Generated UTC: {readiness['generated_at_utc']}",
        "",
        "## Pipeline",
        "",
        "1. Existing ingestion: cleaning, deduplication, audit, and UTC standardization.",
        "2. Cross-dataset overlap audit before treating files as independent issues.",
        "3. Canonical post/account/interaction features with no manual labels overwritten.",
        "4. Initial EDA: counts, relations, hourly activity, and summary artifacts.",
        "5. Automatic pseudo-labels from the existing combined proxy model.",
        "",
        "## Critical Finding",
        "",
        f"- Excluded from independent comparison: `{', '.join(duplicate_batches) or 'none'}`.",
        "- `misi18tokped` overlaps almost completely with `ManfaatnyaDirasakan`; it must not be counted as a separate independent issue during evaluation.",
        "",
        "## Label Policy",
        "",
        "- Files named `*_auto_pseudo_labels.csv` are model-generated candidates, not human ground truth.",
        "- `label_class=Unknown` remains unresolved when proxy probability is between 0.35 and 0.65.",
        "- Existing Batch 2/3 manual labels and canonical files are not modified by this pipeline.",
        "",
        "## Outputs",
        "",
        "- `output/phase2_new_data/phase2_readiness.json`",
        "- `output/phase2_new_data/cross_dataset_overlap.csv`",
        "- `output/phase2_new_data/dataset_summary.csv`",
        "- `output/phase2_new_data/*.png` and relation/hourly CSV files",
        "- `data/features/batch4_*`, `batch5_*`, and `batch6_*`",
        "- `data/labels/batch4_auto_pseudo_labels.csv`, `batch5_auto_pseudo_labels.csv`, and `batch6_auto_pseudo_labels.csv`",
    ]
    report_path = root_path / "reports" / "PHASE2_NEW_DATA_READINESS_REPORT.md"
    report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")
    readiness["artifacts"]["report"] = str(report_path)
    readiness_path.write_text(json.dumps(readiness, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    return readiness


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare and audit the new datasets")
    parser.add_argument("--root", default=None)
    args = parser.parse_args()
    result = run_phase2_new_data(args.root)
    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
