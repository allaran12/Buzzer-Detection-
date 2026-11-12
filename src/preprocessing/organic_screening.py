#!/usr/bin/env python3
"""Conservative screening of supplemental Organic accounts for final training."""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer


FINAL_BATCHES = ("batch2", "batch3", "batch4", "batch5")
ELIGIBLE_ORGANIC_BATCHES = ("batch2", "batch3")
SIMILARITY_THRESHOLD = 0.60


def find_repo_root(root: str | Path | None = None) -> Path:
    if root is not None:
        path = Path(root).resolve()
    else:
        path = Path.cwd().resolve()
        while path != path.parent and not (path / "PRD.md").exists():
            path = path.parent
    if not (path / "PRD.md").exists():
        raise FileNotFoundError("Repository root dengan PRD.md tidak ditemukan")
    return path


def _read(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"File tidak ditemukan: {path}")
    return pd.read_csv(path, dtype="string", keep_default_na=True)


def _normalise_text(values: pd.Series) -> pd.Series:
    return (
        values.fillna("")
        .astype(str)
        .str.lower()
        .str.replace(r"https?://\S+", " ", regex=True)
        .str.replace(r"@\w+", " ", regex=True)
        .str.replace(r"#", " ", regex=False)
        .str.replace(r"[^\w\s]", " ", regex=True)
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
    )


def _numeric(frame: pd.DataFrame, column: str, default: float = 0.0) -> pd.Series:
    return pd.to_numeric(frame.get(column, default), errors="coerce").fillna(default)


def _account_similarity(posts: pd.DataFrame, accounts: pd.DataFrame) -> pd.DataFrame:
    posts = posts.copy()
    posts["account_id"] = posts["account_id"].astype("string").str.strip()
    posts["_normalised_text"] = _normalise_text(posts.get("body_clean", posts.get("text", "")))
    grouped = (
        posts.groupby("account_id", dropna=True)["_normalised_text"]
        .apply(lambda values: " ".join(value for value in values if value))
        .reindex(accounts["account_id"].astype("string"))
        .fillna("")
    )
    if grouped.empty:
        return pd.DataFrame({"account_id": accounts["account_id"].astype("string")})

    vectorizer = TfidfVectorizer(
        analyzer="char_wb",
        ngram_range=(3, 5),
        min_df=1,
        max_features=30000,
        sublinear_tf=True,
    )
    matrix = vectorizer.fit_transform(grouped.tolist())
    similarity = (matrix @ matrix.T).tocsr()
    similarity.setdiag(0)
    similarity.eliminate_zeros()
    max_similarity = np.asarray(similarity.max(axis=1).toarray()).ravel()
    peer_count = np.asarray((similarity >= SIMILARITY_THRESHOLD).sum(axis=1)).ravel()
    exact_peer_count = np.asarray((similarity >= 0.999).sum(axis=1)).ravel()

    unique_ratio = (
        posts.assign(_normalised_text=posts["_normalised_text"])
        .groupby("account_id", dropna=True)["_normalised_text"]
        .agg(lambda values: values.replace("", pd.NA).dropna().nunique() / max(values.replace("", pd.NA).dropna().size, 1))
        .reindex(accounts["account_id"].astype("string"))
        .fillna(0.0)
        .to_numpy(dtype=float)
    )
    return pd.DataFrame({
        "account_id": accounts["account_id"].astype("string").to_numpy(),
        "max_peer_similarity": max_similarity,
        "peer_count_similarity_060": peer_count,
        "exact_peer_count": exact_peer_count,
        "unique_text_ratio": unique_ratio,
    })


def _load_manual_labels(root: Path, batch: str) -> pd.DataFrame:
    path = root / "data" / "labels" / f"{batch}_labeled_canonical.csv"
    if not path.exists():
        return pd.DataFrame(columns=["account_id", "label"])
    labels = _read(path)
    labels["account_id"] = labels["account_id"].astype("string").str.strip()
    labels["label"] = pd.to_numeric(labels["label"], errors="coerce").astype("Int64")
    return labels[["account_id", "label"]]


def _evidence(row: pd.Series) -> str:
    span = float(row["active_span_hours_observed"])
    days = int(row["active_days_observed"])
    return (
        "Supplemental Organic weak label: "
        f"{int(row['n_posts'])} post dalam {span:.2f} jam/{days} hari; "
        f"max peer text similarity {float(row['max_peer_similarity']):.3f} < {SIMILARITY_THRESHOLD:.2f}; "
        f"peer similarity >= {SIMILARITY_THRESHOLD:.2f}: {int(row['peer_count_similarity_060'])}; "
        f"burst ratio 1h {float(row['burst_ratio_1h']):.3f}; "
        f"unique text ratio {float(row['unique_text_ratio']):.3f}. "
        "Bukan ground truth manual dan tetap perlu human review bila dipakai untuk keputusan."
    )


def run_screening(root: str | Path | None = None) -> dict[str, Any]:
    root_path = find_repo_root(root)
    audit_frames: list[pd.DataFrame] = []
    candidates: list[pd.DataFrame] = []

    for batch in FINAL_BATCHES:
        accounts = _read(root_path / "data" / "features" / f"{batch}_account_features.csv")
        posts = _read(root_path / "data" / "features" / f"{batch}_posts_with_features.csv")
        accounts["account_id"] = accounts["account_id"].astype("string").str.strip()
        posts["account_id"] = posts["account_id"].astype("string").str.strip()
        similarity = _account_similarity(posts, accounts)
        manual = _load_manual_labels(root_path, batch).rename(columns={"label": "manual_label"})
        frame = accounts.merge(similarity, on="account_id", how="left", validate="one_to_one")
        frame = frame.merge(manual, on="account_id", how="left", validate="one_to_one")
        frame["dataset_id"] = frame["dataset_id"].fillna(batch)
        frame["issue_id"] = frame["issue_id"].fillna(batch)

        n_posts = _numeric(frame, "n_posts")
        burst = _numeric(frame, "burst_ratio_1h")
        active_span = _numeric(frame, "active_span_hours_observed")
        active_days = _numeric(frame, "active_days_observed")
        frame["screening_status"] = "UNKNOWN"
        frame["screening_reason"] = "Evidence belum cukup untuk weak Organic label"
        frame.loc[frame["manual_label"].notna(), "screening_status"] = "ALREADY_MANUALLY_LABELED"
        frame.loc[frame["manual_label"].notna(), "screening_reason"] = "Manual label dipertahankan"

        eligible_issue = batch in ELIGIBLE_ORGANIC_BATCHES
        eligible = (
            frame["manual_label"].isna()
            & eligible_issue
            & (n_posts >= 2)
            & (frame["max_peer_similarity"] < SIMILARITY_THRESHOLD)
            & (frame["peer_count_similarity_060"] == 0)
            & (frame["exact_peer_count"] == 0)
            & (burst <= 0.5)
            & ((active_span >= 1.0) | (active_days >= 2))
            & (frame["unique_text_ratio"] >= 0.75)
        )
        frame.loc[eligible, "screening_status"] = "ORGANIC_CANDIDATE"
        frame.loc[eligible, "screening_reason"] = "Conservative multi-signal Organic screen"
        frame["batch"] = batch
        audit_frames.append(frame)

        if eligible.any():
            selected = frame.loc[eligible].copy()
            selected["label"] = 0
            selected["label_class"] = "Organic"
            selected["review_status"] = "AUTO_SCREENED_WEAK"
            selected["candidate_type"] = "Supplemental_Organic"
            selected["label_source"] = "organic_screening_v1"
            selected["label_confidence"] = 0.70
            selected["sample_weight"] = 0.35
            selected["evidence"] = selected.apply(_evidence, axis=1)
            selected["notes"] = (
                "Weak label untuk menambah variasi Organic pada training; "
                "tidak dihitung sebagai ground truth evaluasi."
            )
            candidates.append(selected[[
                "account_id", "username", "dataset_id", "issue_id", "label", "label_class",
                "evidence", "notes", "review_status", "candidate_type", "label_source",
                "label_confidence", "sample_weight", "n_posts", "max_peer_similarity",
                "peer_count_similarity_060", "exact_peer_count", "unique_text_ratio",
                "burst_ratio_1h", "active_span_hours_observed", "active_days_observed",
            ]])

    audit = pd.concat(audit_frames, ignore_index=True)
    organic = pd.concat(candidates, ignore_index=True) if candidates else pd.DataFrame()
    if not organic.empty and organic.duplicated(subset=["dataset_id", "account_id"]).any():
        raise ValueError("Supplemental Organic memiliki duplicate dataset_id/account_id")

    labels_dir = root_path / "data" / "labels"
    output_dir = root_path / "output" / "final_model"
    labels_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    organic_path = labels_dir / "final_organic_screened.csv"
    audit_path = labels_dir / "final_organic_screening_audit.csv"
    summary_path = output_dir / "organic_screening_summary.json"
    organic.to_csv(organic_path, index=False, encoding="utf-8-sig")
    audit.to_csv(audit_path, index=False, encoding="utf-8-sig")

    summary = {
        "schema_version": "organic-screening-v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "batches_scanned": list(FINAL_BATCHES),
        "eligible_batches": list(ELIGIBLE_ORGANIC_BATCHES),
        "excluded_from_automatic_organic": {
            "batch4": "Template similarity is pervasive; no automatic Organic weak label added.",
            "batch5": "Template similarity is pervasive; no automatic Organic weak label added.",
            "batch6": "Near-duplicate of batch4 and excluded from independent final training.",
        },
        "accounts_scanned": int(len(audit)),
        "manual_labeled_accounts": int(audit["manual_label"].notna().sum()),
        "organic_candidates": int(len(organic)),
        "candidates_by_batch": {
            str(batch): int((organic["dataset_id"] == batch).sum()) if not organic.empty else 0
            for batch in FINAL_BATCHES
        },
        "candidate_policy": {
            "min_posts": 2,
            "max_peer_similarity": SIMILARITY_THRESHOLD,
            "max_burst_ratio_1h": 0.5,
            "min_active_span_hours_or_days": "1 hour or 2 calendar days",
            "min_unique_text_ratio": 0.75,
            "sample_weight": 0.35,
        },
        "artifacts": {"organic_labels": str(organic_path), "audit": str(audit_path)},
    }
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Screen conservative supplemental Organic accounts")
    parser.add_argument("--root", default=None)
    args = parser.parse_args()
    print(json.dumps(run_screening(args.root), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
