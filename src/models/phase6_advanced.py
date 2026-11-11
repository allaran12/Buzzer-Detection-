#!/usr/bin/env python3
"""Phase 6 advanced-modeling prototype for CoordinX.

The executable path is dependency-light and uses TF-IDF text, temporal sequence
statistics, and graph neighbor statistics as a reproducible fusion proxy. The
artifact records that it is not an IndoBERTweet/LSTM/GraphSAGE model.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import pickle
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


if __name__ == "__main__":
    _src_root = str(Path(__file__).resolve().parents[1])
    if _src_root not in sys.path:
        sys.path.insert(0, _src_root)
    import models as _models_package
    sys.modules.setdefault("models.phase6_advanced", sys.modules[__name__])

SEED = 42
LABELS = [0, 1]
BATCHES = ("batch2", "batch3")
BASE_FEATURES = [
    "avg_tags", "avg_body_len", "url_rate", "avg_words",
    "n_posts", "active_hours", "post_rate", "n_replies", "n_quotes",
    "n_originals", "in_degree", "out_degree", "total_degree", "pagerank",
    "component_size",
]
SEQUENCE_FEATURES = [
    "sequence_len", "mean_interval_hours", "std_interval_hours",
    "min_interval_hours", "max_interval_hours", "burst_ratio_1h",
    "active_span_hours_observed", "active_days_observed", "hour_entropy",
]
GRAPH_FEATURES = [
    "graph_in_degree", "graph_out_degree", "graph_unique_targets",
    "graph_unique_sources", "graph_pagerank", "graph_component_size",
]
MODEL_FEATURES = BASE_FEATURES + SEQUENCE_FEATURES + GRAPH_FEATURES
TEMPORAL_FEATURES = [
    "n_posts", "active_hours", "post_rate", "n_replies", "n_quotes",
    "n_originals", *SEQUENCE_FEATURES,
]
GRAPH_MODEL_FEATURES = [
    "in_degree", "out_degree", "total_degree", "pagerank", "component_size",
    *GRAPH_FEATURES,
]


def find_repo_root(root: str | Path | None = None) -> Path:
    if root is not None:
        path = Path(root).resolve()
        if not (path / "PRD.md").exists():
            raise FileNotFoundError(f"PRD.md tidak ditemukan di {path}")
        return path
    for candidate in [Path.cwd(), *Path.cwd().parents]:
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


def dependency_status() -> dict[str, bool]:
    return {
        name: importlib.util.find_spec(name) is not None
        for name in ("torch", "transformers", "torch_geometric")
    }


class TextColumnExtractor(BaseEstimator, TransformerMixin):
    def fit(self, values, y=None):
        return self

    def transform(self, values):
        if isinstance(values, pd.DataFrame):
            values = values.iloc[:, 0]
        values = np.asarray(values, dtype=object)
        if values.ndim == 2:
            values = values[:, 0]
        return pd.Series(values).fillna("").astype(str).to_numpy()

    def get_feature_names_out(self, input_features=None):
        return np.asarray(input_features if input_features is not None else ["text"])


TextColumnExtractor.__module__ = "models.phase6_advanced"


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"File tidak ditemukan: {path}")
    return pd.read_csv(path, dtype="string", keep_default_na=True)


def _as_numeric(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    frame = frame.copy()
    for column in columns:
        if column not in frame.columns:
            frame[column] = np.nan
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    return frame


def _entropy(values: pd.Series) -> float:
    counts = values.value_counts(normalize=True)
    if counts.empty:
        return 0.0
    return float(-(counts * np.log2(counts)).sum())


def _node_key(account_id: Any, username: Any, username_to_id: dict[str, str]) -> str | None:
    clean_id = normalize_identifier(account_id)
    if clean_id:
        return f"id::{clean_id}"
    if username is not None and not pd.isna(username):
        username_key = str(username).strip().lower()
        mapped_id = username_to_id.get(username_key)
        if mapped_id:
            return f"id::{mapped_id}"
        if username_key:
            return f"user::{username_key}"
    return None


def _target_node_key(account_id: Any, username: Any, username_to_id: dict[str, str]) -> str | None:
    clean_id = normalize_identifier(account_id)
    if clean_id:
        return f"id::{clean_id}"
    if username is not None and not pd.isna(username):
        username_key = str(username).strip().lower()
        mapped_id = username_to_id.get(username_key)
        if mapped_id:
            return f"id::{mapped_id}"
        if username_key:
            return f"user::{username_key}"
    return None


def load_batch(batch_name: str, root: Path) -> pd.DataFrame:
    feature_path = root / "data" / "features" / f"{batch_name}_account_features_with_scores.csv"
    post_path = root / "data" / "features" / f"{batch_name}_posts_with_features.csv"
    canonical_label_path = root / "data" / "labels" / f"{batch_name}_labeled_canonical.csv"
    label_path = canonical_label_path if canonical_label_path.exists() else root / "data" / "labels" / f"{batch_name}_labeled_combined.csv"

    features = read_csv(feature_path)
    labels = read_csv(label_path)
    posts = read_csv(post_path)

    for frame in (features, labels, posts):
        if "username" in frame.columns:
            frame["username"] = frame["username"].astype("string").str.strip()
    features["account_id"] = features.get("account_id", pd.Series(pd.NA, index=features.index)).map(normalize_identifier).astype("string")
    posts["account_id"] = posts.get("account_id", pd.Series(pd.NA, index=posts.index)).map(normalize_identifier).astype("string")
    posts["source_account_id"] = posts.get("source_account_id", posts["account_id"]).map(normalize_identifier).astype("string")
    posts["target_account_id"] = posts.get("target_account_id", pd.Series(pd.NA, index=posts.index)).map(normalize_identifier).astype("string")
    posts["date"] = pd.to_datetime(posts.get("date", posts.get("created")), errors="coerce", utc=True)
    posts["body_clean"] = posts.get("body_clean", posts.get("text", pd.Series("", index=posts.index))).fillna("").astype(str)
    posts["relation_type"] = posts.get("relation_type", pd.Series("original", index=posts.index)).fillna("original").astype(str)
    posts["n_tags"] = pd.to_numeric(posts.get("n_tags", pd.Series(0, index=posts.index)), errors="coerce").fillna(0)
    posts["body_len"] = pd.to_numeric(posts.get("body_len", posts["body_clean"].str.len()), errors="coerce").fillna(0)
    posts["has_url"] = pd.to_numeric(posts.get("has_url", pd.Series(0, index=posts.index)), errors="coerce").fillna(0)

    username_to_id = (
        features.dropna(subset=["username", "account_id"])
        .drop_duplicates("username")
        .set_index("username")["account_id"]
        .astype(str)
        .to_dict()
    )
    post_id_lookup = (
        posts.dropna(subset=["username", "account_id"])
        .drop_duplicates("username")
        .set_index("username")["account_id"]
        .astype(str)
        .to_dict()
    )
    for username, account_id in post_id_lookup.items():
        username_to_id.setdefault(str(username), account_id)

    posts["source_node"] = [
        _node_key(account_id, username, username_to_id)
        for account_id, username in zip(posts["source_account_id"], posts["username"])
    ]
    posts["target_node"] = [
        _target_node_key(account_id, username, username_to_id)
        for account_id, username in zip(posts["target_account_id"], posts.get("target_username", pd.Series(pd.NA, index=posts.index)))
    ]

    sequence_rows = []
    text_rows = []
    for username, group in posts.groupby("username", dropna=True):
        group = group.sort_values("date")
        times = group["date"].dropna()
        intervals = times.diff().dt.total_seconds().div(3600).dropna()
        sequence_rows.append({
            "username": username,
            "sequence_len": int(len(group)),
            "mean_interval_hours": intervals.mean() if not intervals.empty else np.nan,
            "std_interval_hours": intervals.std(ddof=0) if not intervals.empty else np.nan,
            "min_interval_hours": intervals.min() if not intervals.empty else np.nan,
            "max_interval_hours": intervals.max() if not intervals.empty else np.nan,
            "burst_ratio_1h": float((intervals <= 1).mean()) if not intervals.empty else 0.0,
            "active_span_hours_observed": (
                float((times.max() - times.min()).total_seconds() / 3600)
                if len(times) > 1 else 0.0
            ),
            "active_days_observed": int(times.dt.date.nunique()) if not times.empty else 0,
            "hour_entropy": _entropy(times.dt.hour) if not times.empty else 0.0,
        })
        text_rows.append({
            "username": username,
            "text_blob": " ".join(group["body_clean"].tolist()).strip(),
            "observed_url_rate": float(group["has_url"].mean()) if len(group) else 0.0,
            "observed_avg_words": float(group["body_clean"].str.split().str.len().mean()) if len(group) else 0.0,
        })
    sequence = pd.DataFrame(sequence_rows)
    text = pd.DataFrame(text_rows)

    graph = nx.DiGraph()
    source_nodes = posts["source_node"].dropna().unique().tolist()
    graph.add_nodes_from(source_nodes)
    interaction_mask = posts["relation_type"].isin(["reply", "quote"])
    edges = posts.loc[interaction_mask, ["source_node", "target_node"]].dropna().drop_duplicates()
    graph.add_edges_from(edges.itertuples(index=False, name=None))
    undirected = graph.to_undirected()
    pagerank = nx.pagerank(graph, alpha=0.85) if graph.number_of_nodes() else {}
    component_sizes = {}
    for component in nx.connected_components(undirected):
        for node in component:
            component_sizes[node] = len(component)
    graph_rows = []
    for username, account_id in username_to_id.items():
        node = _node_key(account_id, username, username_to_id)
        if node is None:
            continue
        graph_rows.append({
            "username": username,
            "graph_in_degree": float(graph.in_degree(node)) if node in graph else 0.0,
            "graph_out_degree": float(graph.out_degree(node)) if node in graph else 0.0,
            "graph_unique_targets": float(len(set(graph.successors(node)))) if node in graph else 0.0,
            "graph_unique_sources": float(len(set(graph.predecessors(node)))) if node in graph else 0.0,
            "graph_pagerank": float(pagerank.get(node, 0.0)),
            "graph_component_size": float(component_sizes.get(node, 1)),
        })
    graph_frame = pd.DataFrame(graph_rows)
    canonical_graph_columns = ["username", *GRAPH_FEATURES]
    if set(canonical_graph_columns).issubset(features.columns):
        graph_frame = features[canonical_graph_columns].copy()

    labels["label"] = pd.to_numeric(labels.get("label"), errors="coerce")
    labels = labels.dropna(subset=["username", "label"]).copy()
    labels["label"] = labels["label"].astype(int)
    if labels["username"].duplicated().any():
        raise ValueError(f"Duplicate username pada label {batch_name}")

    joined = labels.merge(features, on="username", how="left", suffixes=("_label", ""))
    if "label_label" in joined.columns:
        joined["label"] = joined.pop("label_label")
    joined["label"] = pd.to_numeric(joined["label"], errors="coerce")
    if "account_id_label" in joined.columns:
        joined["account_id"] = joined["account_id"].fillna(joined["account_id_label"])
        joined = joined.drop(columns=["account_id_label"])
    joined["account_id"] = joined["account_id"].fillna(joined["username"].map(username_to_id)).astype("string")
    if "sequence_len" not in joined.columns:
        joined = joined.merge(sequence, on="username", how="left")
    if "text_blob" not in joined.columns:
        joined = joined.merge(text, on="username", how="left")
    if not set(GRAPH_FEATURES).issubset(joined.columns):
        joined = joined.merge(graph_frame, on="username", how="left")
    joined["dataset_id"] = batch_name
    joined["account_group"] = batch_name + "::" + joined["account_id"].fillna(joined["username"])
    joined["first_post"] = pd.to_datetime(joined.get("first_post"), errors="coerce", utc=True)
    joined["last_post"] = pd.to_datetime(joined.get("last_post"), errors="coerce", utc=True)
    joined["text_blob"] = joined.get("text_blob", pd.Series("", index=joined.index)).fillna("").astype(str)
    joined = _as_numeric(joined, MODEL_FEATURES)
    if "total_degree" in joined.columns:
        joined["total_degree"] = joined["total_degree"].fillna(joined["in_degree"].fillna(0) + joined["out_degree"].fillna(0))
    joined["component_size"] = joined["component_size"].fillna(joined["graph_component_size"])
    joined["url_rate"] = joined["url_rate"].fillna(joined["observed_url_rate"] if "observed_url_rate" in joined else 0)
    joined["avg_words"] = joined["avg_words"].fillna(joined["observed_avg_words"] if "observed_avg_words" in joined else 0)
    return joined, posts, {
        "label_path": str(label_path),
        "feature_path": str(feature_path),
        "post_path": str(post_path),
        "invalid_target_account_ids": int(posts.loc[interaction_mask, "target_account_id"].isna().sum()),
        "interaction_rows": int(interaction_mask.sum()),
        "labeled_accounts": int(len(joined)),
        "labeled_single_post_accounts": int((joined["sequence_len"] == 1).sum()),
    }


def load_training_data(root: Path, batches: tuple[str, ...] = BATCHES):
    frames = []
    posts = {}
    readiness = {}
    for batch in batches:
        frame, post_frame, stats = load_batch(batch, root)
        frames.append(frame)
        posts[batch] = post_frame
        readiness[batch] = stats
    data = pd.concat(frames, ignore_index=True)
    data["account_group"] = data["account_group"].astype(str)
    return data, posts, readiness


def numeric_branch(columns: list[str]) -> Pipeline:
    return Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])


def text_branch() -> Pipeline:
    return Pipeline([
        ("extract", TextColumnExtractor()),
        ("tfidf", TfidfVectorizer(
            analyzer="char",
            ngram_range=(3, 5),
            min_df=1,
            max_features=3000,
            sublinear_tf=True,
        )),
    ])


def build_pipeline(branch: str) -> Pipeline:
    transformers = []
    if branch in {"text", "fusion"}:
        transformers.append(("text", text_branch(), ["text_blob"]))
    if branch == "temporal":
        numeric_columns = TEMPORAL_FEATURES
    elif branch == "graph":
        numeric_columns = GRAPH_MODEL_FEATURES
    elif branch == "fusion":
        numeric_columns = MODEL_FEATURES
    else:
        numeric_columns = []
    if numeric_columns:
        transformers.append(("numeric", numeric_branch(numeric_columns), numeric_columns))
    preprocess = ColumnTransformer(transformers=transformers, remainder="drop")
    return Pipeline([
        ("preprocess", preprocess),
        ("model", LogisticRegression(class_weight="balanced", max_iter=2000, random_state=SEED)),
    ])


def _safe_metric(metric_fn, y_true, values, **kwargs) -> float:
    try:
        return float(metric_fn(y_true, values, **kwargs))
    except ValueError:
        return float("nan")


def metrics_from_predictions(y_true, predictions, probabilities) -> dict[str, float | list[list[int]]]:
    return {
        "accuracy": float(accuracy_score(y_true, predictions)),
        "precision_buzzer": _safe_metric(precision_score, y_true, predictions, zero_division=0),
        "recall_buzzer": _safe_metric(recall_score, y_true, predictions, zero_division=0),
        "f1_buzzer": _safe_metric(f1_score, y_true, predictions, zero_division=0),
        "roc_auc": _safe_metric(roc_auc_score, y_true, probabilities),
        "pr_auc": _safe_metric(average_precision_score, y_true, probabilities),
        "confusion_matrix": confusion_matrix(y_true, predictions, labels=LABELS).tolist(),
    }


def evaluate_group_cv(data: pd.DataFrame, branch: str) -> tuple[dict[str, Any], pd.DataFrame]:
    y = data["label"].astype(int).to_numpy()
    groups = data["account_group"].to_numpy()
    splitter = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=SEED)
    predictions = np.full(len(data), -1, dtype=int)
    probabilities = np.full(len(data), np.nan, dtype=float)
    folds = np.full(len(data), -1, dtype=int)
    for fold, (train_idx, test_idx) in enumerate(splitter.split(data, y, groups)):
        model = build_pipeline(branch)
        model.fit(data.iloc[train_idx], y[train_idx])
        predictions[test_idx] = model.predict(data.iloc[test_idx])
        probabilities[test_idx] = model.predict_proba(data.iloc[test_idx])[:, 1]
        folds[test_idx] = fold
    metrics = metrics_from_predictions(y, predictions, probabilities)
    fold_f1 = [
        f1_score(y[folds == fold], predictions[folds == fold], zero_division=0)
        for fold in sorted(set(folds))
    ]
    metrics["fold_f1_mean"] = float(np.mean(fold_f1))
    metrics["fold_f1_std"] = float(np.std(fold_f1))
    export = data[["dataset_id", "account_id", "username", "label"]].copy()
    export["model"] = branch
    export["fold"] = folds
    export["prediction"] = predictions
    export["probability_buzzer"] = probabilities
    return metrics, export


def evaluate_cross_issue(data: pd.DataFrame, branch: str) -> pd.DataFrame:
    rows = []
    for train_batch, test_batch in (("batch2", "batch3"), ("batch3", "batch2")):
        train = data[data["dataset_id"] == train_batch]
        test = data[data["dataset_id"] == test_batch]
        model = build_pipeline(branch)
        model.fit(train, train["label"].astype(int))
        predictions = model.predict(test)
        probabilities = model.predict_proba(test)[:, 1]
        metrics = metrics_from_predictions(test["label"].astype(int), predictions, probabilities)
        rows.append({
            "branch": branch,
            "train_batch": train_batch,
            "test_batch": test_batch,
            **{key: value for key, value in metrics.items() if key != "confusion_matrix"},
        })
    return pd.DataFrame(rows)


def explain_full_model(model: Pipeline, data: pd.DataFrame) -> pd.DataFrame:
    predictions = model.predict(data)
    probabilities = model.predict_proba(data)[:, 1]
    transformed = model.named_steps["preprocess"].transform(data)
    coefficients = model.named_steps["model"].coef_[0]
    names = model.named_steps["preprocess"].get_feature_names_out()
    rows = []
    for index, row in data.reset_index(drop=True).iterrows():
        values = transformed[index].toarray().ravel() if hasattr(transformed[index], "toarray") else np.asarray(transformed[index]).ravel()
        contributions = values * coefficients
        top_indices = np.argsort(contributions)[::-1]
        positive = [
            f"{names[position]} ({contributions[position]:+.3f})"
            for position in top_indices
            if contributions[position] > 0
        ][:5]
        negative = [
            f"{names[position]} ({contributions[position]:+.3f})"
            for position in top_indices[::-1]
            if contributions[position] < 0
        ][:5]
        rows.append({
            "dataset_id": row["dataset_id"],
            "account_id": row["account_id"],
            "username": row["username"],
            "label": int(row["label"]),
            "prediction": int(predictions[index]),
            "probability_buzzer": float(probabilities[index]),
            "positive_evidence": "; ".join(positive),
            "negative_evidence": "; ".join(negative),
        })
    return pd.DataFrame(rows)


def save_confusion_matrix(matrix: list[list[int]], path: Path, title: str) -> None:
    fig, axis = plt.subplots(figsize=(5, 4))
    sns.heatmap(matrix, annot=True, fmt="d", cmap="Blues", cbar=False, ax=axis, xticklabels=["Organic", "Buzzer"], yticklabels=["Organic", "Buzzer"])
    axis.set_title(title)
    axis.set_xlabel("Predicted")
    axis.set_ylabel("Actual")
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def run_phase6(root: str | Path | None = None, batches: tuple[str, ...] = BATCHES) -> dict[str, Any]:
    root_path = find_repo_root(root)
    output_dir = root_path / "output" / "phase6"
    model_dir = root_path / "models"
    report_dir = root_path / "reports"
    output_dir.mkdir(parents=True, exist_ok=True)
    model_dir.mkdir(parents=True, exist_ok=True)

    data, _, readiness = load_training_data(root_path, batches)
    branches = {
        "text_proxy": "text",
        "temporal_proxy": "temporal",
        "graph_proxy": "graph",
        "fusion_proxy": "fusion",
    }
    metric_rows = []
    oof_frames = []
    confusion_by_branch = {}
    for model_name, branch in branches.items():
        metrics, oof = evaluate_group_cv(data, branch)
        metric_rows.append({"model": model_name, **{key: value for key, value in metrics.items() if key != "confusion_matrix"}})
        oof["model"] = model_name
        oof_frames.append(oof)
        confusion_by_branch[model_name] = metrics["confusion_matrix"]
    metrics_frame = pd.DataFrame(metric_rows)
    metrics_frame.to_csv(output_dir / "phase6_group_cv_metrics.csv", index=False)
    oof_frame = pd.concat(oof_frames, ignore_index=True)
    oof_frame.to_csv(output_dir / "phase6_group_cv_oof_predictions.csv", index=False)

    fusion_cross_issue = evaluate_cross_issue(data, "fusion")
    fusion_cross_issue.to_csv(output_dir / "phase6_cross_issue_metrics.csv", index=False)

    fusion_model = build_pipeline("fusion")
    fusion_model.fit(data, data["label"].astype(int))
    artifact = {
        "model": fusion_model,
        "feature_columns": MODEL_FEATURES,
        "sequence_features": SEQUENCE_FEATURES,
        "graph_features": GRAPH_FEATURES,
        "training_rows": int(len(data)),
        "training_batches": sorted(data["dataset_id"].unique().tolist()),
        "random_seed": SEED,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "text_backend": "tfidf_proxy",
        "advanced_backends": {
            "indobertweet": False,
            "lstm": False,
            "graphsage": False,
        },
        "dependency_status": dependency_status(),
        "note": "Phase 6 fusion proxy. It is not a final IndoBERTweet/LSTM/GraphSAGE model.",
    }
    model_path = model_dir / "phase6_fusion_proxy.pkl"
    with model_path.open("wb") as handle:
        pickle.dump(artifact, handle)

    explanations = explain_full_model(fusion_model, data)
    explanations.to_csv(output_dir / "phase6_fusion_explanations.csv", index=False)
    errors = explanations[explanations["label"] != explanations["prediction"]].copy()
    errors["error_type"] = np.where((errors["label"] == 0) & (errors["prediction"] == 1), "false_positive", "false_negative")
    errors.to_csv(output_dir / "phase6_error_analysis.csv", index=False)

    save_confusion_matrix(
        confusion_by_branch["fusion_proxy"],
        output_dir / "phase6_fusion_confusion_matrix.png",
        "Phase 6 Fusion Proxy - Group CV",
    )
    ax = metrics_frame.set_index("model")[["accuracy", "precision_buzzer", "recall_buzzer", "f1_buzzer", "roc_auc", "pr_auc"]].plot(kind="bar", figsize=(12, 6), ylim=(0, 1.05))
    ax.set_title("Phase 6 Branch Comparison - Group CV")
    ax.set_ylabel("Score")
    ax.set_xlabel("")
    ax.tick_params(axis="x", rotation=20)
    ax.legend(title="Metric", bbox_to_anchor=(1.02, 1), loc="upper left")
    plt.tight_layout()
    plt.savefig(output_dir / "phase6_branch_metrics_comparison.png", dpi=180, bbox_inches="tight")
    plt.close()

    readiness_payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "dependency_status": dependency_status(),
        "batches": readiness,
        "training_rows": int(len(data)),
        "training_batches": sorted(data["dataset_id"].unique().tolist()),
        "labeled_single_post_accounts": int((data["sequence_len"] == 1).sum()),
    }
    (output_dir / "phase6_readiness.json").write_text(json.dumps(readiness_payload, indent=2, default=str), encoding="utf-8")

    report = f"""# CoordinX - Phase 6 Advanced Modeling Report

**Generated (UTC):** {readiness_payload['generated_at_utc']}
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

{metrics_frame.to_markdown(index=False, floatfmt='.3f')}

## 3. Cross-Issue Results

{fusion_cross_issue.to_markdown(index=False, floatfmt='.3f')}

## 4. Data Readiness

"""
    for batch, stats in readiness.items():
        report += f"- **{batch}:** {stats['labeled_accounts']} labeled accounts; {stats['labeled_single_post_accounts']} labeled accounts hanya memiliki satu post; {stats['interaction_rows']} interaction rows; {stats['invalid_target_account_ids']} target account IDs tidak dapat dipakai sebagai ID numerik dan diproses melalui fallback username.\n"
    report += f"""
Total training rows: **{len(data)}**. Batch yang sudah digunakan: **{', '.join(sorted(data['dataset_id'].unique()))}**.

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
"""
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "PHASE6_ADVANCED_MODELING_REPORT.md").write_text(report, encoding="utf-8")
    return {
        "metrics": metrics_frame,
        "cross_issue": fusion_cross_issue,
        "readiness": readiness_payload,
        "model_path": str(model_path),
        "report_path": str(report_dir / "PHASE6_ADVANCED_MODELING_REPORT.md"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="CoordinX Phase 6 advanced modeling prototype")
    parser.add_argument("--root", default=None)
    parser.add_argument("--batches", nargs="+", choices=BATCHES, default=list(BATCHES))
    args = parser.parse_args()
    result = run_phase6(args.root, tuple(args.batches))
    print(result["metrics"].round(3).to_string(index=False))
    print(f"Saved model: {result['model_path']}")
    print(f"Saved report: {result['report_path']}")


if __name__ == "__main__":
    main()
