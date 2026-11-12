#!/usr/bin/env python3
"""Temporal LSTM account classifier for Phase 6 smoke testing."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch
from torch import nn
from torch.nn.utils.rnn import pack_padded_sequence, pad_sequence

from models.deep_learning_common import (
    SEED,
    account_key,
    base_readiness,
    classification_metrics,
    labeled_accounts,
    print_metrics,
    prototype_output_dir,
    read_batch_data,
    save_json,
    set_seed,
    stratified_account_split,
    write_confusion_matrix,
    normalize_identifier,
)


SEQUENCE_FEATURES = [
    "n_tags_scaled",
    "body_len_scaled",
    "has_url",
    "is_reply",
    "is_quote",
    "delta_hours_scaled",
    "hour_sin",
    "hour_cos",
]


def _boolean_series(values: pd.Series) -> pd.Series:
    return values.astype("string").str.strip().str.lower().isin({"true", "1", "yes"}).astype(float)


def _build_sequences(
    data: dict[str, pd.DataFrame],
    labels: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, np.ndarray], dict[str, Any]]:
    sequences: dict[str, np.ndarray] = {}
    stats: dict[str, Any] = {"sequence_feature_names": SEQUENCE_FEATURES, "missing_accounts": []}
    for batch, tables in data.items():
        posts = tables["posts"].copy()
        posts["account_id"] = posts["account_id"].map(normalize_identifier)
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
        posts["hour"] = posts["date"].dt.hour + posts["date"].dt.minute / 60.0
        posts["hour_sin"] = np.sin(2 * np.pi * posts["hour"] / 24.0)
        posts["hour_cos"] = np.cos(2 * np.pi * posts["hour"] / 24.0)
        posts["delta_hours"] = posts.groupby("account_key")["date"].diff().dt.total_seconds().div(3600).fillna(0)
        posts["delta_hours_scaled"] = np.log1p(posts["delta_hours"].clip(lower=0)).div(6.0).clip(0, 3)
        posts["n_tags_scaled"] = posts["n_tags"].div(10.0).clip(0, 3)
        posts["body_len_scaled"] = posts["body_len"].div(280.0).clip(0, 4)
        for key, group in posts.groupby("account_key", sort=False):
            values = group[SEQUENCE_FEATURES].to_numpy(dtype=np.float32)
            if len(values):
                sequences[key] = values

    missing = labels.loc[~labels["account_key"].isin(sequences), "account_key"].tolist()
    if missing:
        stats["missing_accounts"] = missing[:10]
        raise ValueError(f"Label tanpa sequence: {missing[:5]}")
    result = labels.copy()
    result["sequence_len"] = result["account_key"].map(lambda key: int(len(sequences[key])))
    stats["labeled_sequence_lengths"] = {
        str(key): int(value) for key, value in result["sequence_len"].value_counts().sort_index().items()
    }
    stats["max_sequence_len"] = int(result["sequence_len"].max())
    return result, sequences, stats


class TemporalLSTMClassifier(nn.Module):
    def __init__(self, input_size: int, hidden_size: int = 32, layers: int = 1, dropout: float = 0.0):
        super().__init__()
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=layers,
            batch_first=True,
            dropout=dropout if layers > 1 else 0.0,
        )
        self.classifier = nn.Sequential(
            nn.LayerNorm(hidden_size),
            nn.Linear(hidden_size, 2),
        )

    def forward(self, sequences: list[torch.Tensor]) -> torch.Tensor:
        lengths = torch.tensor([len(sequence) for sequence in sequences], dtype=torch.long)
        padded = pad_sequence(sequences, batch_first=True)
        packed = pack_padded_sequence(padded, lengths.cpu(), batch_first=True, enforce_sorted=False)
        _, (hidden, _) = self.lstm(packed)
        return self.classifier(hidden[-1])


def _train(
    model: TemporalLSTMClassifier,
    sequences: list[torch.Tensor],
    labels: torch.Tensor,
    epochs: int,
    learning_rate: float,
    device: torch.device,
) -> list[float]:
    model.to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate, weight_decay=1e-4)
    loss_function = nn.CrossEntropyLoss()
    history: list[float] = []
    model.train()
    for _ in range(epochs):
        optimizer.zero_grad()
        logits = model([sequence.to(device) for sequence in sequences])
        loss = loss_function(logits, labels.to(device))
        loss.backward()
        optimizer.step()
        history.append(float(loss.detach().cpu()))
    return history


def run_prototype(
    root: str | Path | None = None,
    hidden_size: int = 32,
    epochs: int = 80,
    learning_rate: float = 0.01,
    test_size: float = 0.3,
    device: str = "cpu",
) -> dict[str, Any]:
    set_seed(SEED)
    data = read_batch_data(root)
    labels = labeled_accounts(data)
    account_frame, sequence_map, sequence_stats = _build_sequences(data, labels)
    train_indices, test_indices = stratified_account_split(account_frame, test_size=test_size)
    sequence_tensors = [torch.tensor(sequence_map[key], dtype=torch.float32) for key in account_frame["account_key"]]
    model = TemporalLSTMClassifier(input_size=len(SEQUENCE_FEATURES), hidden_size=hidden_size)
    history = _train(
        model,
        [sequence_tensors[index] for index in train_indices],
        torch.tensor(account_frame.iloc[train_indices]["label"].to_numpy(dtype=int)),
        epochs=epochs,
        learning_rate=learning_rate,
        device=torch.device(device),
    )
    model.eval()
    with torch.no_grad():
        logits = model([sequence_tensors[index].to(device) for index in test_indices])
        probabilities = torch.softmax(logits, dim=1)[:, 1].cpu().numpy()
    predictions = (probabilities >= 0.5).astype(int)
    true_labels = account_frame.iloc[test_indices]["label"].to_numpy(dtype=int)
    metrics = classification_metrics(true_labels, predictions, probabilities)

    output_dir = prototype_output_dir(root, "temporal_lstm")
    model_dir = output_dir / "model"
    model_dir.mkdir(parents=True, exist_ok=True)
    model_path = model_dir / "temporal_lstm_prototype.pt"
    torch.save({
        "model_type": "temporal_lstm_account_classifier",
        "state_dict": model.state_dict(),
        "input_size": len(SEQUENCE_FEATURES),
        "hidden_size": hidden_size,
        "sequence_features": SEQUENCE_FEATURES,
        "schema_version": "phase6-prototype-v1",
    }, model_path)
    predictions_frame = account_frame.iloc[test_indices][["account_key", "username", "dataset_id", "issue_id", "label", "sequence_len"]].copy()
    predictions_frame["prediction"] = predictions
    predictions_frame["probability_buzzer"] = probabilities
    predictions_frame["split"] = "test"
    predictions_frame.to_csv(output_dir / "test_predictions.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame({"epoch": np.arange(1, len(history) + 1), "loss": history}).to_csv(
        output_dir / "training_history.csv", index=False
    )
    write_confusion_matrix(metrics, output_dir / "confusion_matrix.png", "Temporal LSTM Prototype")

    readiness = base_readiness(
        "Temporal LSTM account sequence classifier",
        root,
        data.keys(),
        metrics,
        {
            "model": str(model_path),
            "test_predictions": str(output_dir / "test_predictions.csv"),
            "training_history": str(output_dir / "training_history.csv"),
            "confusion_matrix": str(output_dir / "confusion_matrix.png"),
        },
        [
            "Prototype only: 70/30 account-level split and full-batch CPU training.",
            "Single-post accounts provide sequence length one and do not validate temporal learning.",
            "Use labeled multi-post accounts as the next data-collection priority.",
        ],
    )
    readiness["data"] = {
        "labeled_accounts": int(len(account_frame)),
        "train_accounts": int(len(train_indices)),
        "test_accounts": int(len(test_indices)),
        "class_counts": {str(key): int(value) for key, value in account_frame["label"].value_counts().sort_index().items()},
        **sequence_stats,
    }
    save_json(output_dir / "readiness.json", readiness)
    print_metrics("Temporal LSTM", metrics)
    return readiness


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the temporal LSTM prototype")
    parser.add_argument("--root", default=None)
    parser.add_argument("--hidden-size", type=int, default=32)
    parser.add_argument("--epochs", type=int, default=80)
    parser.add_argument("--learning-rate", type=float, default=0.01)
    parser.add_argument("--test-size", type=float, default=0.3)
    parser.add_argument("--device", default="cpu")
    args = parser.parse_args()
    run_prototype(**vars(args))


if __name__ == "__main__":
    main()
