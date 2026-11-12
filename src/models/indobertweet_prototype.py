#!/usr/bin/env python3
"""Frozen IndoBERTweet account-level prototype for Phase 6 smoke testing."""
from __future__ import annotations

import argparse
import pickle
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from transformers import AutoModel, AutoTokenizer

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


DEFAULT_CHECKPOINT = "indolem/indobertweet-base-uncased"


def _text_column(posts: pd.DataFrame) -> str:
    for column in ("text", "text_model_input", "body_clean"):
        if column in posts.columns and posts[column].fillna("").astype(str).str.strip().ne("").any():
            return column
    raise ValueError("Tidak ada kolom teks yang dapat dipakai")


def _labeled_post_texts(
    data: dict[str, pd.DataFrame], labels: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows: list[dict[str, Any]] = []
    for batch, tables in data.items():
        posts = tables["posts"].copy()
        posts["account_id"] = posts["account_id"].map(normalize_identifier)
        posts["dataset_id"] = posts["dataset_id"].fillna(batch).astype(str)
        column = _text_column(posts)
        posts["_text"] = posts[column].fillna("").astype(str).str.strip()
        posts["date"] = pd.to_datetime(posts["date"], errors="coerce", utc=True)
        posts["account_key"] = posts.apply(
            lambda row: account_key(row["dataset_id"], row["account_id"]), axis=1
        )
        posts = posts[posts["_text"].ne("")].sort_values(["account_key", "date", "post_id"])
        rows.extend(
            posts[["account_key", "_text"]].rename(columns={"_text": "text"}).to_dict("records")
        )
    post_frame = pd.DataFrame(rows)
    if post_frame.empty:
        raise ValueError("Tidak ada teks postingan berlabel")
    post_frame = post_frame[post_frame["account_key"].isin(labels["account_key"])].reset_index(drop=True)
    counts = post_frame["account_key"].value_counts().rename("n_posts_embedded")
    result = labels.merge(counts, left_on="account_key", right_index=True, how="left", validate="one_to_one")
    missing = result["n_posts_embedded"].isna()
    if missing.any():
        raise ValueError(f"Label tanpa teks: {result.loc[missing, 'account_key'].tolist()[:5]}")
    result["n_posts_embedded"] = result["n_posts_embedded"].astype(int)
    return result, post_frame


def encode_texts(
    texts: list[str],
    checkpoint: str = DEFAULT_CHECKPOINT,
    batch_size: int = 8,
    max_length: int = 128,
    device: str = "cpu",
) -> tuple[np.ndarray, dict[str, Any]]:
    tokenizer = AutoTokenizer.from_pretrained(checkpoint)
    encoder = AutoModel.from_pretrained(checkpoint)
    target_device = torch.device(device)
    encoder.to(target_device)
    encoder.eval()
    for parameter in encoder.parameters():
        parameter.requires_grad = False

    embeddings: list[np.ndarray] = []
    with torch.no_grad():
        for start in range(0, len(texts), batch_size):
            batch = texts[start:start + batch_size]
            encoded = tokenizer(
                batch,
                padding=True,
                truncation=True,
                max_length=max_length,
                return_tensors="pt",
            )
            encoded = {key: value.to(target_device) for key, value in encoded.items()}
            output = encoder(**encoded).last_hidden_state
            mask = encoded["attention_mask"].unsqueeze(-1).to(output.dtype)
            pooled = (output * mask).sum(dim=1) / mask.sum(dim=1).clamp_min(1.0)
            embeddings.append(pooled.cpu().numpy())
    return np.vstack(embeddings), {
        "checkpoint": checkpoint,
        "hidden_size": int(encoder.config.hidden_size),
        "max_length": max_length,
        "pooling": "attention_mask_mean",
        "device": str(target_device),
    }


def pool_post_embeddings(
    post_frame: pd.DataFrame,
    post_embeddings: np.ndarray,
    account_keys: pd.Series,
) -> np.ndarray:
    embedding_by_key: dict[str, np.ndarray] = {}
    for key, indices in post_frame.groupby("account_key", sort=False).groups.items():
        embedding_by_key[str(key)] = post_embeddings[np.asarray(list(indices), dtype=int)].mean(axis=0)
    missing = [key for key in account_keys if str(key) not in embedding_by_key]
    if missing:
        raise ValueError(f"Embedding account tidak ditemukan: {missing[:5]}")
    return np.vstack([embedding_by_key[str(key)] for key in account_keys])


def run_prototype(
    root: str | Path | None = None,
    checkpoint: str = DEFAULT_CHECKPOINT,
    batch_size: int = 8,
    max_length: int = 128,
    test_size: float = 0.3,
    device: str = "cpu",
) -> dict[str, Any]:
    set_seed(SEED)
    data = read_batch_data(root)
    labels = labeled_accounts(data)
    account_frame, post_frame = _labeled_post_texts(data, labels)
    post_embeddings, encoder_meta = encode_texts(
        post_frame["text"].tolist(),
        checkpoint=checkpoint,
        batch_size=batch_size,
        max_length=max_length,
        device=device,
    )
    embeddings = pool_post_embeddings(post_frame, post_embeddings, account_frame["account_key"])
    train_indices, test_indices = stratified_account_split(account_frame, test_size=test_size)
    classifier = Pipeline([
        ("scale", StandardScaler()),
        ("classifier", LogisticRegression(
            max_iter=1000,
            class_weight="balanced",
            random_state=SEED,
        )),
    ])
    classifier.fit(embeddings[train_indices], account_frame.iloc[train_indices]["label"].to_numpy(dtype=int))
    probabilities = classifier.predict_proba(embeddings[test_indices])[:, 1]
    predictions = (probabilities >= 0.5).astype(int)
    metrics = classification_metrics(
        account_frame.iloc[test_indices]["label"].to_numpy(dtype=int), predictions, probabilities
    )

    output_dir = prototype_output_dir(root, "indobertweet")
    model_dir = output_dir / "model"
    model_dir.mkdir(parents=True, exist_ok=True)
    model_path = model_dir / "indobertweet_prototype.pkl"
    with model_path.open("wb") as handle:
        pickle.dump({
            "model_type": "indobertweet_frozen_account_pooling",
            "classifier": classifier,
            "encoder": encoder_meta,
            "schema_version": "phase6-prototype-v1",
            "feature_policy": "account_mean_pool_of_post_embeddings",
        }, handle)

    embedding_path = output_dir / "labeled_account_embeddings.npz"
    np.savez_compressed(
        embedding_path,
        embeddings=embeddings,
        account_key=account_frame["account_key"].to_numpy(dtype=str),
        label=account_frame["label"].to_numpy(dtype=int),
    )
    predictions_frame = account_frame.iloc[test_indices][["account_key", "username", "dataset_id", "issue_id", "label"]].copy()
    predictions_frame["prediction"] = predictions
    predictions_frame["probability_buzzer"] = probabilities
    predictions_frame["split"] = "test"
    predictions_frame.to_csv(output_dir / "test_predictions.csv", index=False, encoding="utf-8-sig")
    write_confusion_matrix(metrics, output_dir / "confusion_matrix.png", "IndoBERTweet Prototype")

    readiness = base_readiness(
        "IndoBERTweet frozen encoder + account pooling + LogisticRegression",
        root,
        data.keys(),
        metrics,
        {
            "model": str(model_path),
            "embeddings": str(embedding_path),
            "test_predictions": str(output_dir / "test_predictions.csv"),
            "confusion_matrix": str(output_dir / "confusion_matrix.png"),
        },
        [
            "Prototype only: encoder is frozen and classifier uses 70/30 account-level split.",
            "Text column prefers raw text to preserve hashtags, mentions, emoji, and URL markers.",
            "This is not a fine-tuned final IndoBERTweet model.",
        ],
    )
    readiness["encoder"] = encoder_meta
    readiness["data"] = {
        "labeled_accounts": int(len(account_frame)),
        "train_accounts": int(len(train_indices)),
        "test_accounts": int(len(test_indices)),
        "class_counts": {str(key): int(value) for key, value in account_frame["label"].value_counts().sort_index().items()},
    }
    save_json(output_dir / "readiness.json", readiness)
    print_metrics("IndoBERTweet", metrics)
    return readiness


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the frozen IndoBERTweet prototype")
    parser.add_argument("--root", default=None)
    parser.add_argument("--checkpoint", default=DEFAULT_CHECKPOINT)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--max-length", type=int, default=128)
    parser.add_argument("--test-size", type=float, default=0.3)
    parser.add_argument("--device", default="cpu")
    args = parser.parse_args()
    run_prototype(**vars(args))


if __name__ == "__main__":
    main()
