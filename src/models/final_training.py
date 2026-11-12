#!/usr/bin/env python3
"""Train and evaluate the CoordinX research-final three-branch model.

Manual labels are gold data. Supplemental Organic records are weak labels used
only during training with a reduced sample weight; evaluation remains gold-only.
"""
from __future__ import annotations

import argparse
import json
import os
import pickle
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from torch import nn

from models.deep_learning_common import (
    SEED,
    account_key,
    classification_metrics,
    set_seed,
    stratified_account_split,
    write_confusion_matrix,
)
from models.graphsage_prototype import GraphSAGEClassifier, _build_graph
from models.indobertweet_prototype import (
    DEFAULT_CHECKPOINT,
    encode_texts,
    pool_post_embeddings,
)
from models.phase6_advanced import MODEL_FEATURES
from models.temporal_lstm_prototype import (
    SEQUENCE_FEATURES,
    TemporalLSTMClassifier,
    _boolean_series,
)


FINAL_BATCHES = ("batch2", "batch3", "batch4", "batch5")
WEAK_LABEL_PATH = "data/labels/final_organic_screened.csv"
MODEL_VERSION = "coordinx-final-v1.0.0"
SCHEMA_VERSION = "coordinx-final-output-v1"


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


def _normalise_id(value: Any) -> str | None:
    if value is None or pd.isna(value):
        return None
    text = str(value).strip()
    if not text or text.lower() in {"nan", "none", "<na>"}:
        return None
    return text[:-2] if text.endswith(".0") and text[:-2].isdigit() else text


def _load_data(root: Path) -> tuple[dict[str, dict[str, pd.DataFrame]], pd.DataFrame, pd.DataFrame]:
    data: dict[str, dict[str, pd.DataFrame]] = {}
    account_frames: list[pd.DataFrame] = []
    manual_frames: list[pd.DataFrame] = []
    for batch in FINAL_BATCHES:
        features = root / "data" / "features"
        labels_dir = root / "data" / "labels"
        tables = {
            "posts": _read(features / f"{batch}_posts_with_features.csv"),
            "accounts": _read(features / f"{batch}_account_features.csv"),
            "interactions": _read(features / f"{batch}_interactions.csv"),
        }
        data[batch] = tables
        accounts = tables["accounts"].copy()
        accounts["account_id"] = accounts["account_id"].map(_normalise_id)
        accounts["dataset_id"] = accounts["dataset_id"].fillna(batch).astype(str)
        accounts["issue_id"] = accounts["issue_id"].fillna(batch).astype(str)
        accounts["account_key"] = accounts.apply(
            lambda row: account_key(row["dataset_id"], row["account_id"]), axis=1
        )
        account_frames.append(accounts)
        label_path = labels_dir / f"{batch}_labeled_canonical.csv"
        if label_path.exists():
            labels = _read(label_path)
            labels["account_id"] = labels["account_id"].map(_normalise_id)
            labels["dataset_id"] = labels["dataset_id"].fillna(batch).astype(str)
            labels["issue_id"] = labels["issue_id"].fillna(batch).astype(str)
            labels["label"] = pd.to_numeric(labels["label"], errors="coerce")
            labels = labels.dropna(subset=["account_id", "label"]).copy()
            labels["label"] = labels["label"].astype(int)
            labels["account_key"] = labels.apply(
                lambda row: account_key(row["dataset_id"], row["account_id"]), axis=1
            )
            labels["is_gold"] = True
            labels["sample_weight"] = 1.0
            labels["label_source_final"] = "manual_canonical"
            manual_frames.append(labels)

    accounts = pd.concat(account_frames, ignore_index=True).drop_duplicates("account_key")
    manual = pd.concat(manual_frames, ignore_index=True) if manual_frames else pd.DataFrame()
    if manual.empty:
        raise ValueError("Tidak ada manual gold label")

    weak_path = root / WEAK_LABEL_PATH
    weak = _read(weak_path) if weak_path.exists() else pd.DataFrame()
    if not weak.empty:
        weak["account_id"] = weak["account_id"].map(_normalise_id)
        weak["dataset_id"] = weak["dataset_id"].astype(str)
        weak["issue_id"] = weak["issue_id"].fillna(weak["dataset_id"]).astype(str)
        weak["label"] = pd.to_numeric(weak["label"], errors="coerce")
        weak = weak.dropna(subset=["account_id", "label"]).copy()
        weak["label"] = weak["label"].astype(int)
        weak["account_key"] = weak.apply(
            lambda row: account_key(row["dataset_id"], row["account_id"]), axis=1
        )
        weak["is_gold"] = False
        weak["sample_weight"] = pd.to_numeric(weak.get("sample_weight", 0.35), errors="coerce").fillna(0.35)
        weak["label_source_final"] = "organic_screening_v1"
        weak = weak[~weak["account_key"].isin(set(manual["account_key"]))].copy()

    labels = pd.concat([manual, weak], ignore_index=True, sort=False)
    if labels["account_key"].duplicated().any():
        raise ValueError("Label final duplicate pada dataset_id/account_id")
    labels = labels[labels["account_key"].isin(set(accounts["account_key"]))].copy()
    if labels["label"].nunique() < 2:
        raise ValueError("Final training membutuhkan dua kelas")
    return data, accounts, labels


def _gold_split(labels: pd.DataFrame, test_size: float) -> tuple[set[str], set[str]]:
    gold = labels[labels["is_gold"]].reset_index(drop=True)
    train_indices, test_indices = stratified_account_split(gold, test_size=test_size)
    train_keys = set(gold.iloc[train_indices]["account_key"])
    test_keys = set(gold.iloc[test_indices]["account_key"])
    train_keys.update(labels.loc[~labels["is_gold"], "account_key"])
    if train_keys & test_keys:
        raise ValueError("Gold train/test overlap")
    return train_keys, test_keys


def _label_map(labels: pd.DataFrame) -> dict[str, int]:
    return dict(zip(labels["account_key"], labels["label"].astype(int)))


def _weight_map(labels: pd.DataFrame) -> dict[str, float]:
    return dict(zip(labels["account_key"], pd.to_numeric(labels["sample_weight"], errors="coerce").fillna(1.0)))


def _all_post_texts(
    data: dict[str, dict[str, pd.DataFrame]], accounts: pd.DataFrame,
) -> tuple[pd.DataFrame, np.ndarray, dict[str, Any]]:
    rows: list[dict[str, str]] = []
    for batch, tables in data.items():
        posts = tables["posts"].copy()
        posts["account_id"] = posts["account_id"].map(_normalise_id)
        posts["dataset_id"] = posts["dataset_id"].fillna(batch).astype(str)
        posts["account_key"] = posts.apply(
            lambda row: account_key(row["dataset_id"], row["account_id"]), axis=1
        )
        preferred = "text" if "text" in posts.columns else "body_clean"
        posts["_text"] = posts[preferred].fillna("").astype(str).str.strip()
        if "body_clean" in posts.columns:
            fallback = posts["body_clean"].fillna("").astype(str).str.strip()
            posts.loc[posts["_text"].eq(""), "_text"] = fallback.loc[posts["_text"].eq("")]
        posts = posts[posts["_text"].ne("")]
        rows.extend(posts[["account_key", "_text"]].rename(columns={"_text": "text"}).to_dict("records"))
    post_frame = pd.DataFrame(rows)
    if post_frame.empty:
        raise ValueError("Tidak ada teks untuk IndoBERTweet")
    counts = post_frame["account_key"].value_counts()
    missing = accounts.loc[~accounts["account_key"].isin(counts.index), "account_key"].tolist()
    if missing:
        raise ValueError(f"Account tanpa teks: {missing[:5]}")
    embeddings, encoder_meta = encode_texts(
        post_frame["text"].tolist(),
        checkpoint=DEFAULT_CHECKPOINT,
        batch_size=32,
        max_length=128,
        device="cpu",
    )
    pooled = pool_post_embeddings(post_frame, embeddings, accounts["account_key"])
    return post_frame, pooled, encoder_meta


def _text_classifier() -> Pipeline:
    return Pipeline([
        ("scale", StandardScaler()),
        ("classifier", LogisticRegression(max_iter=1000, class_weight="balanced", random_state=SEED)),
    ])


def _fit_text(
    embeddings: np.ndarray,
    accounts: pd.DataFrame,
    labels: pd.DataFrame,
    train_keys: set[str],
) -> Pipeline:
    label_lookup = _label_map(labels)
    weight_lookup = _weight_map(labels)
    keys = accounts["account_key"].tolist()
    indices = [index for index, key in enumerate(keys) if key in train_keys and key in label_lookup]
    values = np.asarray([label_lookup[key] for key in accounts.iloc[indices]["account_key"]], dtype=int)
    weights = np.asarray([weight_lookup[key] for key in accounts.iloc[indices]["account_key"]], dtype=float)
    classifier = _text_classifier()
    classifier.fit(embeddings[indices], values, classifier__sample_weight=weights)
    return classifier


def _sequence_map(
    data: dict[str, dict[str, pd.DataFrame]], accounts: pd.DataFrame,
) -> dict[str, np.ndarray]:
    sequences: dict[str, np.ndarray] = {}
    for batch, tables in data.items():
        posts = tables["posts"].copy()
        posts["account_id"] = posts["account_id"].map(_normalise_id)
        posts["dataset_id"] = posts["dataset_id"].fillna(batch).astype(str)
        posts["account_key"] = posts.apply(
            lambda row: account_key(row["dataset_id"], row["account_id"]), axis=1
        )
        posts["date"] = pd.to_datetime(posts["date"], errors="coerce", utc=True)
        posts = posts.dropna(subset=["date"]).sort_values(["account_key", "date", "post_id"])
        posts["n_tags"] = pd.to_numeric(posts.get("n_tags", 0), errors="coerce").fillna(0)
        posts["body_len"] = pd.to_numeric(posts.get("body_len", 0), errors="coerce").fillna(0)
        posts["has_url"] = _boolean_series(posts.get("has_url", pd.Series(False, index=posts.index)))
        posts["is_reply"] = _boolean_series(posts.get("is_reply", pd.Series(False, index=posts.index)))
        posts["is_quote"] = _boolean_series(posts.get("is_quote", pd.Series(False, index=posts.index)))
        hour = posts["date"].dt.hour + posts["date"].dt.minute / 60.0
        posts["hour_sin"] = np.sin(2 * np.pi * hour / 24.0)
        posts["hour_cos"] = np.cos(2 * np.pi * hour / 24.0)
        delta = posts.groupby("account_key")["date"].diff().dt.total_seconds().div(3600).fillna(0)
        posts["delta_hours_scaled"] = np.log1p(delta.clip(lower=0)).div(6.0).clip(0, 3)
        posts["n_tags_scaled"] = posts["n_tags"].div(10.0).clip(0, 3)
        posts["body_len_scaled"] = posts["body_len"].div(280.0).clip(0, 4)
        for key, group in posts.groupby("account_key", sort=False):
            values = group[SEQUENCE_FEATURES].to_numpy(dtype=np.float32)
            if len(values):
                sequences[str(key)] = values
    missing = [key for key in accounts["account_key"] if key not in sequences]
    if missing:
        raise ValueError(f"Account tanpa sequence: {missing[:5]}")
    return sequences


def _train_lstm(
    model: TemporalLSTMClassifier,
    sequences: list[torch.Tensor],
    labels: np.ndarray,
    train_indices: list[int],
    sample_weights: np.ndarray,
    epochs: int,
    learning_rate: float,
) -> list[float]:
    set_seed(SEED)
    model.to("cpu")
    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate, weight_decay=1e-4)
    train_labels = torch.tensor(labels[train_indices], dtype=torch.long)
    class_counts = torch.bincount(train_labels, minlength=2).float()
    class_weights = class_counts.sum() / class_counts.clamp_min(1.0)
    class_weights = class_weights / class_weights.mean()
    criterion = nn.CrossEntropyLoss(weight=class_weights, reduction="none")
    example_weights = torch.tensor(sample_weights[train_indices], dtype=torch.float32)
    history: list[float] = []
    for _ in range(epochs):
        model.train()
        optimizer.zero_grad()
        logits = model([sequences[index] for index in train_indices])
        losses = criterion(logits, train_labels)
        loss = (losses * example_weights).mean()
        loss.backward()
        optimizer.step()
        history.append(float(loss.detach()))
    return history


def _predict_lstm(model: TemporalLSTMClassifier, sequences: list[torch.Tensor]) -> np.ndarray:
    model.eval()
    probabilities: list[np.ndarray] = []
    with torch.no_grad():
        for start in range(0, len(sequences), 128):
            logits = model(sequences[start:start + 128])
            probabilities.append(torch.softmax(logits, dim=1)[:, 1].numpy())
    return np.concatenate(probabilities)


def _train_graph(
    model: GraphSAGEClassifier,
    graph: dict[str, Any],
    labels: pd.DataFrame,
    epochs: int,
    learning_rate: float,
) -> list[float]:
    set_seed(SEED)
    features = graph["features"]
    target = graph["labels"]
    edge_index = graph["edge_index"]
    train_indices = graph["train_indices"]
    weight_lookup = _weight_map(labels)
    node_weights = torch.tensor(
        [weight_lookup.get(key, 1.0) for key in graph["node_order"]], dtype=torch.float32
    )
    train_labels = target[train_indices]
    class_counts = torch.bincount(train_labels, minlength=2).float()
    class_weights = class_counts.sum() / class_counts.clamp_min(1.0)
    class_weights = class_weights / class_weights.mean()
    criterion = nn.CrossEntropyLoss(weight=class_weights, reduction="none")
    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate, weight_decay=1e-4)
    history: list[float] = []
    model.to("cpu")
    for _ in range(epochs):
        model.train()
        optimizer.zero_grad()
        logits, _ = model(features, edge_index)
        losses = criterion(logits[train_indices], target[train_indices])
        loss = (losses * node_weights[train_indices]).mean()
        loss.backward()
        optimizer.step()
        history.append(float(loss.detach()))
    return history


def _predict_graph(model: GraphSAGEClassifier, graph: dict[str, Any]) -> np.ndarray:
    model.eval()
    with torch.no_grad():
        logits, _ = model(graph["features"], graph["edge_index"])
        return torch.softmax(logits, dim=1)[:, 1].numpy()


def _evaluate(
    name: str,
    probabilities: np.ndarray,
    accounts: pd.DataFrame,
    labels: pd.DataFrame,
    test_keys: set[str],
) -> tuple[dict[str, Any], pd.DataFrame]:
    label_lookup = _label_map(labels)
    indices = [index for index, key in enumerate(accounts["account_key"]) if key in test_keys]
    y_true = np.asarray([label_lookup[accounts.iloc[index]["account_key"]] for index in indices], dtype=int)
    y_prob = probabilities[indices]
    y_pred = (y_prob >= 0.5).astype(int)
    metrics = classification_metrics(y_true, y_pred, y_prob)
    predictions = pd.DataFrame({
        "account_key": accounts.iloc[indices]["account_key"].to_numpy(),
        "label": y_true,
        "probability_buzzer": y_prob,
        "prediction": y_pred,
        "model": name,
    })
    return metrics, predictions


def _graph_eval(
    name: str,
    probabilities: np.ndarray,
    graph: dict[str, Any],
    labels: pd.DataFrame,
    test_keys: set[str],
) -> tuple[dict[str, Any], pd.DataFrame]:
    label_lookup = _label_map(labels)
    indices = [index for index, key in enumerate(graph["node_order"]) if key in test_keys]
    y_true = np.asarray([label_lookup[graph["node_order"][index]] for index in indices], dtype=int)
    y_prob = probabilities[indices]
    y_pred = (y_prob >= 0.5).astype(int)
    metrics = classification_metrics(y_true, y_pred, y_prob)
    predictions = pd.DataFrame({
        "account_key": [graph["node_order"][index] for index in indices],
        "label": y_true,
        "probability_buzzer": y_prob,
        "prediction": y_pred,
        "model": name,
    })
    return metrics, predictions


def _save_metrics_plot(metrics: pd.DataFrame, path: Path) -> None:
    columns = ["accuracy", "precision_buzzer", "recall_buzzer", "f1_buzzer", "roc_auc", "pr_auc"]
    axis = metrics.set_index("model")[columns].plot(kind="bar", figsize=(12, 5), ylim=(0, 1), rot=0)
    axis.set_title("CoordinX Final Model - Gold Holdout Metrics")
    axis.set_ylabel("Score")
    axis.set_xlabel("")
    axis.grid(axis="y", alpha=0.25)
    axis.legend(loc="lower right")
    figure = axis.get_figure()
    figure.tight_layout()
    figure.savefig(path, dpi=180)
    plt.close(figure)


def _build_output(
    root: Path,
    accounts: pd.DataFrame,
    labels: pd.DataFrame,
    text_prob: np.ndarray,
    temporal_prob: np.ndarray,
    graph_prob_by_key: dict[str, float],
    model_version: str,
) -> pd.DataFrame:
    output = accounts[[
        "account_key", "account_id", "username", "dataset_id", "issue_id", "n_posts",
        "post_rate", "avg_tags", "avg_body_len", "n_replies", "n_quotes",
        "burst_ratio_1h", "active_span_hours_observed", "active_days_observed",
        "in_degree", "out_degree", "total_degree", "component_size",
    ]].copy()
    output["indobertweet_probability"] = text_prob
    output["temporal_lstm_probability"] = temporal_prob
    output["graphsage_probability"] = output["account_key"].map(graph_prob_by_key).fillna(0.5)
    output["probability_buzzer"] = (
        0.4 * output["indobertweet_probability"]
        + 0.3 * output["temporal_lstm_probability"]
        + 0.3 * output["graphsage_probability"]
    ).clip(0, 1)
    output["coordination_score"] = (output["probability_buzzer"] * 100).round(2)
    output["confidence"] = (output["probability_buzzer"] - 0.5).abs().mul(2).round(4)
    output["prediction"] = np.select(
        [output["probability_buzzer"] >= 0.65, output["probability_buzzer"] <= 0.35],
        ["Buzzer", "Organic"],
        default="Review",
    )
    output["risk_level"] = np.select(
        [output["probability_buzzer"] >= 0.65, output["probability_buzzer"] <= 0.35],
        ["high", "low"],
        default="medium",
    )
    output["review_status"] = np.where(output["prediction"].eq("Review"), "REVIEW_REQUIRED", "MODEL_OUTPUT")

    audit_path = root / "data" / "labels" / "final_organic_screening_audit.csv"
    if audit_path.exists():
        audit = _read(audit_path)
        audit["account_id"] = audit["account_id"].map(_normalise_id)
        audit["dataset_id"] = audit["dataset_id"].astype(str)
        output = output.merge(
            audit[["account_id", "dataset_id", "max_peer_similarity", "peer_count_similarity_060", "unique_text_ratio"]],
            on=["account_id", "dataset_id"], how="left", validate="one_to_one",
        )
    else:
        output["max_peer_similarity"] = np.nan
        output["peer_count_similarity_060"] = np.nan
        output["unique_text_ratio"] = np.nan

    label_metadata = labels[["account_key", "label", "is_gold", "label_source_final", "review_status", "evidence"]].copy()
    label_metadata = label_metadata.rename(columns={"label": "known_label", "review_status": "label_review_status"})
    output = output.merge(label_metadata, on="account_key", how="left", validate="one_to_one")

    post_rows: list[dict[str, str]] = []
    for batch in FINAL_BATCHES:
        posts = _read(root / "data" / "features" / f"{batch}_posts_with_features.csv")
        posts["account_id"] = posts["account_id"].map(_normalise_id)
        posts["dataset_id"] = posts["dataset_id"].fillna(batch).astype(str)
        posts["_text"] = posts.get("body_clean", posts.get("text", "")).fillna("").astype(str).str.strip()
        for (account_id, dataset_id), group in posts.groupby(["account_id", "dataset_id"], dropna=True):
            values = [value for value in group["_text"].tolist() if value]
            post_rows.append({
                "account_id": account_id,
                "dataset_id": dataset_id,
                "sample_posts": " || ".join(values[:3]),
            })
    output = output.merge(pd.DataFrame(post_rows), on=["account_id", "dataset_id"], how="left", validate="one_to_one")

    def explanations(row: pd.Series) -> str:
        values: list[str] = []
        if float(row.get("max_peer_similarity", 0) or 0) >= 0.75:
            values.append(f"kemiripan teks lintas akun tinggi ({float(row['max_peer_similarity']):.2f})")
        if int(row.get("peer_count_similarity_060", 0) or 0) > 0:
            values.append(f"memiliki {int(row['peer_count_similarity_060'])} peer dengan similarity >= 0.60")
        if float(row.get("burst_ratio_1h", 0) or 0) >= 0.5 and int(row.get("n_posts", 0) or 0) >= 2:
            values.append(f"burst temporal tinggi ({float(row['burst_ratio_1h']):.2f})")
        if int(row.get("total_degree", 0) or 0) >= 3:
            values.append(f"interaksi graph relatif tinggi (degree {int(row['total_degree'])})")
        if not values:
            values.append("tidak ada satu bukti koordinasi dominan pada fitur ringkas")
        return " | ".join(values)

    output["explanation"] = output.apply(explanations, axis=1)
    output["branch_scores"] = output.apply(
        lambda row: json.dumps({
            "indobertweet": round(float(row["indobertweet_probability"]), 4),
            "temporal_lstm": round(float(row["temporal_lstm_probability"]), 4),
            "graphsage": round(float(row["graphsage_probability"]), 4),
        }, ensure_ascii=False), axis=1,
    )
    output["model_version"] = model_version
    output["schema_version"] = SCHEMA_VERSION
    output["prediction_timestamp_utc"] = datetime.now(timezone.utc).isoformat()
    return output


def run_final_training(
    root: str | Path | None = None,
    test_size: float = 0.30,
    lstm_epochs: int = 80,
    graphsage_epochs: int = 100,
) -> dict[str, Any]:
    root_path = find_repo_root(root)
    set_seed(SEED)
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    data, accounts, labels = _load_data(root_path)
    train_keys, test_keys = _gold_split(labels, test_size)
    label_lookup = _label_map(labels)
    sample_lookup = _weight_map(labels)

    output_dir = root_path / "output" / "final_model"
    model_dir = root_path / "models" / "final"
    output_dir.mkdir(parents=True, exist_ok=True)
    model_dir.mkdir(parents=True, exist_ok=True)

    # IndoBERTweet branch: frozen encoder, account pooling, weighted classifier.
    _, embeddings, encoder_meta = _all_post_texts(data, accounts)
    text_eval_model = _fit_text(embeddings, accounts, labels, train_keys)
    text_prob_eval = text_eval_model.predict_proba(embeddings)[:, 1]
    text_metrics, text_test = _evaluate("IndoBERTweet", text_prob_eval, accounts, labels, test_keys)
    text_model = _fit_text(embeddings, accounts, labels, set(labels["account_key"]))
    text_prob_final = text_model.predict_proba(embeddings)[:, 1]
    text_path = model_dir / "indobertweet_final.pkl"
    with text_path.open("wb") as handle:
        pickle.dump({
            "model_type": "indobertweet_frozen_account_pooling",
            "classifier": text_model,
            "encoder": encoder_meta,
            "schema_version": SCHEMA_VERSION,
            "model_version": MODEL_VERSION,
            "training_labels": {"gold": int(labels["is_gold"].sum()), "weak": int((~labels["is_gold"]).sum())},
            "weak_label_policy": "sample_weight=0.35; excluded from gold evaluation",
        }, handle)
    np.savez_compressed(
        output_dir / "indobertweet_account_embeddings.npz",
        embeddings=embeddings,
        account_key=accounts["account_key"].to_numpy(dtype=str),
    )

    # Temporal LSTM branch.
    sequence_map = _sequence_map(data, accounts)
    sequences = [torch.tensor(sequence_map[key], dtype=torch.float32) for key in accounts["account_key"]]
    labels_array = np.asarray([label_lookup.get(key, -1) for key in accounts["account_key"]], dtype=int)
    weights_array = np.asarray([sample_lookup.get(key, 0.0) for key in accounts["account_key"]], dtype=float)
    train_indices = [index for index, key in enumerate(accounts["account_key"]) if key in train_keys]
    temporal_eval_model = TemporalLSTMClassifier(input_size=len(SEQUENCE_FEATURES), hidden_size=32)
    temporal_history_eval = _train_lstm(
        temporal_eval_model, sequences, labels_array, train_indices, weights_array, lstm_epochs, 0.01,
    )
    temporal_prob_eval = _predict_lstm(temporal_eval_model, sequences)
    temporal_metrics, temporal_test = _evaluate("Temporal LSTM", temporal_prob_eval, accounts, labels, test_keys)
    temporal_model = TemporalLSTMClassifier(input_size=len(SEQUENCE_FEATURES), hidden_size=32)
    temporal_history = _train_lstm(
        temporal_model, sequences, labels_array,
        [index for index, key in enumerate(accounts["account_key"]) if key in set(labels["account_key"])],
        weights_array, lstm_epochs, 0.01,
    )
    temporal_prob_final = _predict_lstm(temporal_model, sequences)
    temporal_path = model_dir / "temporal_lstm_final.pt"
    torch.save({
        "model_type": "temporal_lstm_account_classifier",
        "state_dict": temporal_model.state_dict(),
        "input_size": len(SEQUENCE_FEATURES),
        "hidden_size": 32,
        "sequence_features": SEQUENCE_FEATURES,
        "schema_version": SCHEMA_VERSION,
        "model_version": MODEL_VERSION,
    }, temporal_path)
    pd.DataFrame({"epoch": np.arange(1, len(temporal_history) + 1), "loss": temporal_history}).to_csv(
        output_dir / "temporal_lstm_training_history.csv", index=False,
    )

    # GraphSAGE branch. Unlabeled graph nodes participate in message passing.
    graph_labels = labels[["account_key", "label"]].copy()
    graph_train_keys = set(train_keys)
    graph_test_keys = set(test_keys)
    graph_eval, graph_stats = _build_graph(data, graph_labels, split_keys=(graph_train_keys, graph_test_keys))
    graph_eval_model = GraphSAGEClassifier(input_size=len(MODEL_FEATURES), hidden_size=32)
    graph_history_eval = _train_graph(graph_eval_model, graph_eval, labels, graphsage_epochs, 0.01)
    graph_prob_eval = _predict_graph(graph_eval_model, graph_eval)
    graph_metrics, graph_test = _graph_eval("GraphSAGE", graph_prob_eval, graph_eval, labels, test_keys)

    graph_all, graph_all_stats = _build_graph(
        data, graph_labels, split_keys=(set(labels["account_key"]), set()),
    )
    graph_model = GraphSAGEClassifier(input_size=len(MODEL_FEATURES), hidden_size=32)
    graph_history = _train_graph(graph_model, graph_all, labels, graphsage_epochs, 0.01)
    graph_prob_final = _predict_graph(graph_model, graph_all)
    graph_path = model_dir / "graphsage_final.pt"
    torch.save({
        "model_type": "graphsage_account_classifier",
        "state_dict": graph_model.state_dict(),
        "input_size": len(MODEL_FEATURES),
        "hidden_size": 32,
        "feature_names": MODEL_FEATURES,
        "node_order": graph_all["node_order"],
        "imputer_statistics": graph_all["imputer"].statistics_.tolist(),
        "scaler_mean": graph_all["scaler"].mean_.tolist(),
        "scaler_scale": graph_all["scaler"].scale_.tolist(),
        "schema_version": SCHEMA_VERSION,
        "model_version": MODEL_VERSION,
    }, graph_path)
    pd.DataFrame({"epoch": np.arange(1, len(graph_history) + 1), "loss": graph_history}).to_csv(
        output_dir / "graphsage_training_history.csv", index=False,
    )

    graph_prob_eval_by_key = {
        key: float(graph_prob_eval[index]) for index, key in enumerate(graph_eval["node_order"])
    }
    test_frame = text_test[["account_key", "label"]].copy()
    test_frame["indobertweet_probability"] = test_frame["account_key"].map(
        dict(zip(text_test["account_key"], text_test["probability_buzzer"]))
    )
    test_frame["temporal_lstm_probability"] = test_frame["account_key"].map(
        dict(zip(temporal_test["account_key"], temporal_test["probability_buzzer"]))
    )
    test_frame["graphsage_probability"] = test_frame["account_key"].map(graph_prob_eval_by_key)
    test_frame["probability_buzzer"] = (
        0.4 * test_frame["indobertweet_probability"]
        + 0.3 * test_frame["temporal_lstm_probability"]
        + 0.3 * test_frame["graphsage_probability"]
    )
    fusion_metrics = classification_metrics(
        test_frame["label"], (test_frame["probability_buzzer"] >= 0.5).astype(int), test_frame["probability_buzzer"],
    )

    metrics_rows = []
    for name, metrics in (("IndoBERTweet", text_metrics), ("Temporal LSTM", temporal_metrics), ("GraphSAGE", graph_metrics), ("Fusion", fusion_metrics)):
        metrics_rows.append({"model": name, **metrics})
    metrics_frame = pd.DataFrame(metrics_rows)
    metrics_path = output_dir / "final_gold_holdout_metrics.csv"
    metrics_frame.to_csv(metrics_path, index=False)
    _save_metrics_plot(metrics_frame, output_dir / "final_gold_holdout_metrics.png")
    for name, metrics in (("indobertweet", text_metrics), ("temporal_lstm", temporal_metrics), ("graphsage", graph_metrics), ("fusion", fusion_metrics)):
        write_confusion_matrix(metrics, output_dir / f"{name}_confusion_matrix.png", f"Final {name} - Gold Holdout")

    graph_prob_by_key = {
        key: float(graph_prob_final[index]) for index, key in enumerate(graph_all["node_order"])
    }
    predictions = _build_output(
        root_path, accounts, labels, text_prob_final, temporal_prob_final,
        graph_prob_by_key, MODEL_VERSION,
    )
    predictions_path = output_dir / "final_predictions.csv"
    predictions.to_csv(predictions_path, index=False, encoding="utf-8-sig")
    review_path = output_dir / "final_review_queue.csv"
    predictions[predictions["review_status"] == "REVIEW_REQUIRED"].sort_values(
        "coordination_score", ascending=False,
    ).to_csv(review_path, index=False, encoding="utf-8-sig")

    counts = predictions["prediction"].value_counts().to_dict()
    readiness = {
        "status": "RESEARCH_FINAL_READY_FOR_WEB_INTEGRATION",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "model_version": MODEL_VERSION,
        "schema_version": SCHEMA_VERSION,
        "training_batches": list(FINAL_BATCHES),
        "batch6_policy": "excluded because it overlaps batch4 and is not an independent issue",
        "accounts_total": int(len(accounts)),
        "gold_labels": int(labels["is_gold"].sum()),
        "weak_labels": int((~labels["is_gold"]).sum()),
        "gold_class_counts": {str(k): int(v) for k, v in labels.loc[labels["is_gold"], "label"].value_counts().sort_index().items()},
        "weak_class_counts": {str(k): int(v) for k, v in labels.loc[~labels["is_gold"], "label"].value_counts().sort_index().items()},
        "gold_holdout": {"test_accounts": int(len(test_keys)), "metrics": metrics_rows},
        "prediction_counts": {str(key): int(value) for key, value in counts.items()},
        "fusion_policy": {
            "indobertweet": 0.4,
            "temporal_lstm": 0.3,
            "graphsage": 0.3,
            "buzzer_threshold": 0.65,
            "organic_threshold": 0.35,
            "review_interval": "0.35 <= probability_buzzer < 0.65",
        },
        "graph": graph_all_stats,
        "artifacts": {
            "indobertweet_model": str(text_path),
            "temporal_lstm_model": str(temporal_path),
            "graphsage_model": str(graph_path),
            "metrics": str(metrics_path),
            "predictions": str(predictions_path),
            "review_queue": str(review_path),
        },
        "output_columns": list(predictions.columns),
        "notes": [
            "Manual labels are the only gold evaluation labels.",
            "Supplemental Organic accounts are conservative weak labels with sample weight 0.35.",
            "The three branches are research-final artifacts; no automatic label is a legal or factual verdict.",
            "Web integration is intentionally not performed in this phase.",
        ],
    }
    readiness_path = output_dir / "final_readiness.json"
    readiness_path.write_text(json.dumps(readiness, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    report_path = root_path / "reports" / "FINAL_MODEL_READINESS_REPORT.md"
    report_path.write_text(_report(readiness, metrics_frame, predictions), encoding="utf-8")
    return {"readiness": readiness, "metrics": metrics_frame, "predictions": predictions, "report_path": report_path}


def _report(readiness: dict[str, Any], metrics: pd.DataFrame, predictions: pd.DataFrame) -> str:
    lines = [
        "# CoordinX - Final Three-Branch Model Readiness",
        "",
        f"**Generated (UTC):** {readiness['generated_at_utc']}",
        f"**Model version:** `{readiness['model_version']}`",
        "",
        "## Planning and output contract",
        "",
        "Output per account includes `prediction` (Buzzer/Organic/Review), `coordination_score` (0-100), `probability_buzzer`, `confidence`, `risk_level`, three branch probabilities, evidence summary, sample posts, and human-review status.",
        "",
        "## Data policy",
        "",
        f"- Accounts scanned: **{readiness['accounts_total']}** across `{', '.join(readiness['training_batches'])}`.",
        f"- Gold labels: **{readiness['gold_labels']}**; weak Organic labels: **{readiness['weak_labels']}**.",
        "- Batch 6 is excluded because it overlaps Batch 4 and is not an independent issue.",
        "- Weak Organic labels are training support only and are excluded from gold holdout evaluation.",
        "",
        "## Gold holdout metrics",
        "",
        metrics.to_markdown(index=False),
        "",
        "## Model branches",
        "",
        "1. **IndoBERTweet:** frozen Indonesian social-media encoder, post embeddings mean-pooled at account level, weighted Logistic Regression head.",
        "2. **Temporal LSTM:** ordered post sequence with hashtag, length, URL, relation, interval, and cyclical hour features.",
        "3. **GraphSAGE:** account graph from valid reply/quote edges; unlabeled nodes participate in message passing.",
        "4. **Fusion:** 0.4 IndoBERTweet + 0.3 Temporal LSTM + 0.3 GraphSAGE; uncertain scores route to Review.",
        "",
        "## Readiness boundary",
        "",
        "This phase produces reproducible research-final checkpoints and a web-consumable output contract. It does not yet modify `/web`; integration starts only after the user approves the final phase.",
        "",
        "## Artifacts",
        "",
    ]
    lines.extend(f"- `{path}`" for path in readiness["artifacts"].values())
    lines.extend([
        "- `output/final_model/*_confusion_matrix.png`",
        "- `output/final_model/final_gold_holdout_metrics.png`",
        "- `output/final_model/final_predictions.csv`",
    ])
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Train CoordinX final IndoBERTweet, Temporal LSTM, and GraphSAGE")
    parser.add_argument("--root", default=None)
    parser.add_argument("--test-size", type=float, default=0.30)
    parser.add_argument("--lstm-epochs", type=int, default=80)
    parser.add_argument("--graphsage-epochs", type=int, default=100)
    args = parser.parse_args()
    result = run_final_training(**vars(args))
    print(json.dumps(result["readiness"], indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
