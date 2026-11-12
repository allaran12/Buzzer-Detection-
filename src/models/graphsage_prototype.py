#!/usr/bin/env python3
"""GraphSAGE node classifier for Phase 6 smoke testing."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from torch import nn
from torch_geometric.nn import SAGEConv

from models.deep_learning_common import (
    BATCHES,
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
from models.phase6_advanced import MODEL_FEATURES


class GraphSAGEClassifier(nn.Module):
    def __init__(self, input_size: int, hidden_size: int = 32, dropout: float = 0.2):
        super().__init__()
        self.conv1 = SAGEConv(input_size, hidden_size)
        self.conv2 = SAGEConv(hidden_size, hidden_size)
        self.dropout = nn.Dropout(dropout)
        self.classifier = nn.Linear(hidden_size, 2)

    def forward(self, features: torch.Tensor, edge_index: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        hidden = self.conv1(features, edge_index).relu()
        hidden = self.dropout(hidden)
        hidden = self.conv2(hidden, edge_index).relu()
        return self.classifier(hidden), hidden


def _valid_edge_mask(values: pd.Series) -> pd.Series:
    return values.astype("string").str.strip().str.lower().isin({"true", "1", "yes"})


def _build_graph(
    data: dict[str, pd.DataFrame],
    labels: pd.DataFrame,
    split_keys: tuple[set[str], set[str]] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    account_tables: list[pd.DataFrame] = []
    edge_tables: list[pd.DataFrame] = []
    for batch, tables in data.items():
        accounts = tables["accounts"].copy()
        accounts["account_id"] = accounts["account_id"].map(normalize_identifier)
        accounts["dataset_id"] = accounts["dataset_id"].fillna(batch).astype(str)
        accounts["account_key"] = accounts.apply(
            lambda row: account_key(row["dataset_id"], row["account_id"]), axis=1
        )
        account_tables.append(accounts)
        interactions = tables["interactions"].copy()
        interactions = interactions[_valid_edge_mask(interactions["is_valid_edge"])].copy()
        interactions["dataset_id"] = interactions["dataset_id"].fillna(batch).astype(str)
        interactions["source_account_id"] = interactions["source_account_id"].map(normalize_identifier)
        interactions["target_account_id"] = interactions["target_account_id"].map(normalize_identifier)
        interactions = interactions.dropna(subset=["source_account_id", "target_account_id"])
        if not interactions.empty:
            interactions["source_key"] = interactions.apply(
                lambda row: account_key(row["dataset_id"], row["source_account_id"]), axis=1
            )
            interactions["target_key"] = interactions.apply(
                lambda row: account_key(row["dataset_id"], row["target_account_id"]), axis=1
            )
        else:
            interactions["source_key"] = pd.Series(dtype="string")
            interactions["target_key"] = pd.Series(dtype="string")
        edge_tables.append(interactions)

    accounts = pd.concat(account_tables, ignore_index=True).drop_duplicates("account_key")
    interactions = pd.concat(edge_tables, ignore_index=True) if edge_tables else pd.DataFrame()
    node_keys = set(accounts["account_key"].tolist())
    if not interactions.empty:
        node_keys.update(interactions["source_key"].tolist())
        node_keys.update(interactions["target_key"].tolist())
    node_order = sorted(node_keys)
    node_to_index = {key: index for index, key in enumerate(node_order)}

    feature_frame = accounts.set_index("account_key").reindex(node_order)
    numeric = feature_frame.reindex(columns=MODEL_FEATURES).apply(pd.to_numeric, errors="coerce")
    label_frame = labels.set_index("account_key").reindex(node_order)
    labeled_mask = label_frame["label"].notna().to_numpy()
    label_values = pd.to_numeric(label_frame["label"], errors="coerce").fillna(-1).to_numpy(dtype=np.int64)
    if labeled_mask.sum() < 4 or len(np.unique(label_values[labeled_mask])) < 2:
        raise ValueError("GraphSAGE membutuhkan minimal dua kelas berlabel")

    label_indices = np.flatnonzero(labeled_mask)
    if split_keys is None:
        label_split_frame = pd.DataFrame({
            "account_key": np.asarray(node_order, dtype=object)[label_indices],
            "label": label_values[label_indices],
        })
        train_local, test_local = stratified_account_split(label_split_frame, test_size=0.3)
        train_indices = label_indices[train_local]
        test_indices = label_indices[test_local]
    else:
        train_keys, test_keys = split_keys
        train_indices = np.asarray(
            [node_to_index[key] for key in train_keys if key in node_to_index and labeled_mask[node_to_index[key]]],
            dtype=int,
        )
        test_indices = np.asarray(
            [node_to_index[key] for key in test_keys if key in node_to_index and labeled_mask[node_to_index[key]]],
            dtype=int,
        )
        if len(train_indices) < 2 or len(np.unique(label_values[train_indices])) < 2:
            raise ValueError("GraphSAGE split custom membutuhkan dua kelas pada train")

    imputer = SimpleImputer(strategy="median")
    scaler = StandardScaler()
    imputer.fit(numeric.iloc[train_indices])
    scaled = scaler.fit_transform(imputer.transform(numeric.iloc[train_indices]))
    all_features = scaler.transform(imputer.transform(numeric))

    edge_pairs: list[tuple[int, int]] = []
    if not interactions.empty:
        for source, target in interactions[["source_key", "target_key"]].itertuples(index=False):
            source_index = node_to_index[source]
            target_index = node_to_index[target]
            edge_pairs.extend([(source_index, target_index), (target_index, source_index)])
    edge_index = torch.tensor(edge_pairs, dtype=torch.long).t().contiguous()
    if edge_index.numel() == 0:
        edge_index = torch.empty((2, 0), dtype=torch.long)
    graph = {
        "node_order": node_order,
        "features": torch.tensor(all_features, dtype=torch.float32),
        "labels": torch.tensor(label_values, dtype=torch.long),
        "labeled_mask": torch.tensor(labeled_mask, dtype=torch.bool),
        "train_indices": torch.tensor(train_indices, dtype=torch.long),
        "test_indices": torch.tensor(test_indices, dtype=torch.long),
        "edge_index": edge_index,
        "imputer": imputer,
        "scaler": scaler,
    }
    stats = {
        "nodes": len(node_order),
        "account_feature_nodes": int(accounts["account_key"].isin(node_order).sum()),
        "valid_edge_events": int(len(interactions)),
        "message_passing_edges": int(edge_index.shape[1]),
        "labeled_nodes": int(labeled_mask.sum()),
        "train_labeled_nodes": int(len(train_indices)),
        "test_labeled_nodes": int(len(test_indices)),
        "unlabeled_nodes": int((~labeled_mask).sum()),
        "feature_names": MODEL_FEATURES,
        "edge_policy": "valid reply/quote edges with reverse direction added for message passing",
    }
    return graph, stats


def _train(
    model: GraphSAGEClassifier,
    graph: dict[str, Any],
    epochs: int,
    learning_rate: float,
    device: torch.device,
) -> list[float]:
    features = graph["features"].to(device)
    labels = graph["labels"].to(device)
    edge_index = graph["edge_index"].to(device)
    train_indices = graph["train_indices"].to(device)
    class_counts = torch.bincount(labels[train_indices], minlength=2).float()
    weights = class_counts.sum() / class_counts.clamp_min(1.0)
    weights = weights / weights.mean()
    loss_function = nn.CrossEntropyLoss(weight=weights)
    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate, weight_decay=1e-4)
    history: list[float] = []
    model.to(device)
    for _ in range(epochs):
        model.train()
        optimizer.zero_grad()
        logits, _ = model(features, edge_index)
        loss = loss_function(logits[train_indices], labels[train_indices])
        loss.backward()
        optimizer.step()
        history.append(float(loss.detach().cpu()))
    return history


def run_prototype(
    root: str | Path | None = None,
    hidden_size: int = 32,
    epochs: int = 120,
    learning_rate: float = 0.01,
    device: str = "cpu",
) -> dict[str, Any]:
    set_seed(SEED)
    data = read_batch_data(root)
    labels = labeled_accounts(data)
    graph, graph_stats = _build_graph(data, labels)
    model = GraphSAGEClassifier(input_size=len(MODEL_FEATURES), hidden_size=hidden_size)
    history = _train(
        model,
        graph,
        epochs=epochs,
        learning_rate=learning_rate,
        device=torch.device(device),
    )
    model.eval()
    with torch.no_grad():
        logits, embeddings = model(graph["features"].to(device), graph["edge_index"].to(device))
        probabilities = torch.softmax(logits, dim=1)[:, 1].cpu().numpy()
    test_indices = graph["test_indices"].cpu().numpy()
    true_labels = graph["labels"][test_indices].cpu().numpy()
    test_probabilities = probabilities[test_indices]
    predictions = (test_probabilities >= 0.5).astype(int)
    metrics = classification_metrics(true_labels, predictions, test_probabilities)

    output_dir = prototype_output_dir(root, "graphsage")
    model_dir = output_dir / "model"
    model_dir.mkdir(parents=True, exist_ok=True)
    model_path = model_dir / "graphsage_prototype.pt"
    torch.save({
        "model_type": "graphsage_account_classifier",
        "state_dict": model.state_dict(),
        "input_size": len(MODEL_FEATURES),
        "hidden_size": hidden_size,
        "feature_names": MODEL_FEATURES,
        "node_order": graph["node_order"],
        "imputer": graph["imputer"],
        "scaler": graph["scaler"],
        "schema_version": "phase6-prototype-v1",
    }, model_path)
    node_frame = pd.DataFrame({
        "account_key": graph["node_order"],
        "is_labeled": graph["labeled_mask"].cpu().numpy(),
        "label": graph["labels"].cpu().numpy(),
        "probability_buzzer": probabilities,
    })
    node_frame["prediction"] = (node_frame["probability_buzzer"] >= 0.5).astype(int)
    node_frame.to_csv(output_dir / "node_predictions.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame({"epoch": np.arange(1, len(history) + 1), "loss": history}).to_csv(
        output_dir / "training_history.csv", index=False
    )
    np.save(output_dir / "test_node_embeddings.npy", embeddings[test_indices].cpu().numpy())
    write_confusion_matrix(metrics, output_dir / "confusion_matrix.png", "GraphSAGE Prototype")

    readiness = base_readiness(
        "GraphSAGE account node classifier",
        root,
        data.keys(),
        metrics,
        {
            "model": str(model_path),
            "node_predictions": str(output_dir / "node_predictions.csv"),
            "test_embeddings": str(output_dir / "test_node_embeddings.npy"),
            "training_history": str(output_dir / "training_history.csv"),
            "confusion_matrix": str(output_dir / "confusion_matrix.png"),
        },
        [
            "Prototype only: semi-supervised transductive split with loss restricted to train-labeled nodes.",
            "Unlabeled nodes remain in message passing to preserve graph structure.",
            "Cross-issue and inductive edge-holdout evaluation are still required before production use.",
        ],
    )
    readiness["data"] = graph_stats
    save_json(output_dir / "readiness.json", readiness)
    print_metrics("GraphSAGE", metrics)
    return readiness


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the GraphSAGE prototype")
    parser.add_argument("--root", default=None)
    parser.add_argument("--hidden-size", type=int, default=32)
    parser.add_argument("--epochs", type=int, default=120)
    parser.add_argument("--learning-rate", type=float, default=0.01)
    parser.add_argument("--device", default="cpu")
    args = parser.parse_args()
    run_prototype(**vars(args))


if __name__ == "__main__":
    main()
