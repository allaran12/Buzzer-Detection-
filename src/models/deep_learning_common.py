#!/usr/bin/env python3
"""Shared data, split, metric, and artifact helpers for Phase 6 prototypes."""
from __future__ import annotations

import json
import pickle
import random
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split


SEED = 42
BATCHES = ("batch2", "batch3")


def find_repo_root(root: str | Path | None = None) -> Path:
    if root is not None:
        path = Path(root).resolve()
        if not (path / "PRD.md").exists():
            raise FileNotFoundError(f"PRD.md tidak ditemukan di {path}")
        return path
    for candidate in (Path.cwd(), *Path.cwd().parents):
        if (candidate / "PRD.md").exists() and (candidate / "data").exists():
            return candidate
    raise FileNotFoundError("Repository root tidak ditemukan")


def normalize_identifier(value: Any) -> str | None:
    if value is None or pd.isna(value):
        return None
    text = str(value).strip()
    if not text or text.lower() in {"nan", "none", "<na>"}:
        return None
    if re.search(r"[eE][+-]?\d+", text):
        return None
    return re.sub(r"\.0$", "", text)


def account_key(dataset_id: Any, account_id: Any) -> str:
    dataset = str(dataset_id).strip()
    identifier = normalize_identifier(account_id)
    if identifier is None:
        raise ValueError("account_id kosong saat membuat account key")
    return f"{dataset}:{identifier}"


def set_seed(seed: int = SEED) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.use_deterministic_algorithms(False)


def read_batch_data(root: str | Path | None = None, batches: Iterable[str] = BATCHES) -> dict[str, pd.DataFrame]:
    root_path = find_repo_root(root)
    result: dict[str, pd.DataFrame] = {}
    for batch in batches:
        if batch not in BATCHES:
            raise ValueError(f"Batch tidak dikenal: {batch}")
        features = root_path / "data" / "features"
        labels_dir = root_path / "data" / "labels"
        result[batch] = {
            "posts": pd.read_csv(features / f"{batch}_posts_with_features.csv", dtype="string"),
            "accounts": pd.read_csv(features / f"{batch}_account_features.csv", dtype="string"),
            "interactions": pd.read_csv(features / f"{batch}_interactions.csv", dtype="string"),
            "labels": pd.read_csv(labels_dir / f"{batch}_labeled_canonical.csv", dtype="string"),
        }
    return result


def labeled_accounts(data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for batch, tables in data.items():
        labels = tables["labels"].copy()
        labels["account_id"] = labels["account_id"].map(normalize_identifier)
        labels["label"] = pd.to_numeric(labels["label"], errors="coerce")
        labels = labels.dropna(subset=["account_id", "label"]).copy()
        labels["label"] = labels["label"].astype(int)
        labels["dataset_id"] = labels["dataset_id"].fillna(batch).astype(str)
        labels["account_key"] = labels.apply(
            lambda row: account_key(row["dataset_id"], row["account_id"]), axis=1
        )
        frames.append(labels)
    if not frames:
        raise ValueError("Tidak ada label canonical yang dapat dipakai")
    result = pd.concat(frames, ignore_index=True)
    if result["account_key"].duplicated().any():
        duplicates = result.loc[result["account_key"].duplicated(), "account_key"].tolist()
        raise ValueError(f"Label duplicate pada account key: {duplicates[:5]}")
    return result


def stratified_account_split(
    frame: pd.DataFrame,
    test_size: float = 0.3,
    seed: int = SEED,
) -> tuple[np.ndarray, np.ndarray]:
    indices = np.arange(len(frame))
    labels = frame["label"].to_numpy(dtype=int)
    stratify = labels if len(np.unique(labels)) == 2 and np.min(np.bincount(labels)) >= 2 else None
    train_indices, test_indices = train_test_split(
        indices,
        test_size=test_size,
        random_state=seed,
        stratify=stratify,
    )
    return np.sort(train_indices), np.sort(test_indices)


def classification_metrics(
    y_true: Iterable[int],
    y_pred: Iterable[int],
    y_prob: Iterable[float],
) -> dict[str, Any]:
    true = np.asarray(list(y_true), dtype=int)
    pred = np.asarray(list(y_pred), dtype=int)
    prob = np.asarray(list(y_prob), dtype=float)
    result: dict[str, Any] = {
        "n": int(len(true)),
        "accuracy": float(accuracy_score(true, pred)),
        "precision_buzzer": float(precision_score(true, pred, zero_division=0)),
        "recall_buzzer": float(recall_score(true, pred, zero_division=0)),
        "f1_buzzer": float(f1_score(true, pred, zero_division=0)),
        "confusion_matrix": confusion_matrix(true, pred, labels=[0, 1]).tolist(),
    }
    if len(np.unique(true)) == 2:
        result["roc_auc"] = float(roc_auc_score(true, prob))
        result["pr_auc"] = float(average_precision_score(true, prob))
    else:
        result["roc_auc"] = None
        result["pr_auc"] = None
    return result


def write_confusion_matrix(metrics: dict[str, Any], path: Path, title: str) -> None:
    matrix = np.asarray(metrics["confusion_matrix"], dtype=int)
    figure, axis = plt.subplots(figsize=(5, 4))
    image = axis.imshow(matrix, cmap="Blues")
    axis.set_title(title)
    axis.set_xlabel("Predicted")
    axis.set_ylabel("Actual")
    axis.set_xticks([0, 1], ["Organic", "Buzzer"])
    axis.set_yticks([0, 1], ["Organic", "Buzzer"])
    threshold = matrix.max() / 2 if matrix.size else 0
    for row in range(matrix.shape[0]):
        for column in range(matrix.shape[1]):
            axis.text(
                column,
                row,
                str(matrix[row, column]),
                ha="center",
                va="center",
                color="white" if matrix[row, column] > threshold else "black",
            )
    figure.colorbar(image, ax=axis, fraction=0.046, pad=0.04)
    figure.tight_layout()
    figure.savefig(path, dpi=180)
    plt.close(figure)


def prototype_output_dir(root: str | Path | None, name: str) -> Path:
    path = find_repo_root(root) / "output" / "phase6_prototypes" / name
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, default=str), encoding="utf-8")


def save_pickle(path: Path, payload: Any) -> None:
    with path.open("wb") as handle:
        pickle.dump(payload, handle)


def base_readiness(
    name: str,
    root: str | Path | None,
    batches: Iterable[str],
    metrics: dict[str, Any],
    artifacts: dict[str, str],
    notes: list[str],
) -> dict[str, Any]:
    return {
        "status": "PROTOTYPE_ONLY",
        "model": name,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "repository": str(find_repo_root(root)),
        "batches": list(batches),
        "metrics": metrics,
        "artifacts": artifacts,
        "notes": notes,
    }


def print_metrics(name: str, metrics: dict[str, Any]) -> None:
    print(f"=== {name} PROTOTYPE ===")
    for key in ("n", "accuracy", "precision_buzzer", "recall_buzzer", "f1_buzzer", "roc_auc", "pr_auc"):
        print(f"{key}: {metrics.get(key)}")
    print("confusion_matrix:")
    print(np.asarray(metrics["confusion_matrix"]))


def ensure_src_path(root: str | Path | None = None) -> Path:
    src = find_repo_root(root) / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))
    return src
