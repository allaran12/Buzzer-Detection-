"""Live inference adapter for scraped X posts.

The training notebooks use canonical account, temporal, and graph features.
This module builds the same feature contract from a small live scrape so the
web service does not fall back to mock scores or the old heuristic pipeline.
"""
from __future__ import annotations

import json
import pickle
import re
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any

import networkx as nx
import numpy as np
import pandas as pd
import torch
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from torch import nn
from transformers import AutoModel, AutoTokenizer

SRC_DIR = Path(__file__).resolve().parents[1]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from features.canonical_features import _account_features, _build_graph
from models.deep_learning_common import account_key, normalize_identifier
from models.graphsage_prototype import GraphSAGEClassifier
from models.indobertweet_prototype import DEFAULT_CHECKPOINT, pool_post_embeddings
from models.phase6_advanced import MODEL_FEATURES
from models.temporal_lstm_prototype import SEQUENCE_FEATURES, TemporalLSTMClassifier


MODEL_VERSION = "coordinx-final-v1.0.0"
SCHEMA_VERSION = "coordinx-final-output-v1"
FUSION_WEIGHTS = {"indobertweet": 0.4, "temporal_lstm": 0.3, "graphsage": 0.3}


def _normalise(value: Any) -> str | None:
    return normalize_identifier(value)


def _bool_series(values: pd.Series) -> pd.Series:
    return values.astype("string").str.strip().str.lower().isin({"true", "1", "yes"})


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or pd.isna(value):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or pd.isna(value):
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def prepare_live_posts(
    frame: pd.DataFrame,
    dataset_id: str = "live",
    issue_id: str = "live",
) -> pd.DataFrame:
    """Normalise scraper/CSV rows into the canonical post feature contract."""
    posts = frame.copy()
    aliases = {
        "id": "post_id",
        "tweet_id": "post_id",
        "user_id": "account_id",
        "source_account_id": "account_id",
        "raw_text": "text",
        "content": "text",
        "created_at": "date",
        "timestamp": "date",
    }
    for source, target in aliases.items():
        if target not in posts.columns and source in posts.columns:
            posts[target] = posts[source]

    defaults: dict[str, Any] = {
        "post_id": pd.NA,
        "account_id": pd.NA,
        "username": "unknown",
        "text": "",
        "date": pd.NaT,
        "created": pd.NaT,
        "followers": 0,
        "following": 0,
        "statuses": 0,
        "bio": "",
        "avatar": "",
        "relation_type": "original",
        "target_post_id": pd.NA,
        "target_account_id": pd.NA,
        "target_username": pd.NA,
        "is_rt": False,
        "is_reply": False,
        "is_quote": False,
        "url": "",
    }
    for column, default in defaults.items():
        if column not in posts.columns:
            posts[column] = default

    posts["post_id"] = posts["post_id"].map(_normalise).astype("string")
    posts["account_id"] = posts["account_id"].map(_normalise).astype("string")
    posts["username"] = posts["username"].fillna("unknown").astype("string").str.strip()
    posts["text"] = posts["text"].fillna("").astype("string")
    posts["date"] = pd.to_datetime(posts["date"], errors="coerce", utc=True)
    posts["created"] = pd.to_datetime(posts["created"], errors="coerce", utc=True)
    for column in ["followers", "following", "statuses"]:
        posts[column] = pd.to_numeric(posts[column], errors="coerce").fillna(0)

    for column in ["is_rt", "is_reply", "is_quote"]:
        posts[column] = _bool_series(posts[column])

    relation = posts["relation_type"].fillna("original").astype("string").str.lower().str.strip()
    relation = relation.mask(posts["is_rt"], "retweet")
    relation = relation.mask(posts["is_quote"], "quote")
    relation = relation.mask(posts["is_reply"], "reply")
    posts["relation_type"] = relation

    username_to_id = (
        posts.dropna(subset=["username", "account_id"])
        .assign(username_key=lambda value: value["username"].str.lower())
        .drop_duplicates("username_key")
        .set_index("username_key")["account_id"]
        .to_dict()
    )
    posts["target_account_id"] = posts["target_account_id"].map(_normalise)
    target_username = posts["target_username"].astype("string").str.strip()
    posts["target_username"] = target_username
    posts["target_account_id"] = posts["target_account_id"].fillna(
        target_username.str.lower().map(username_to_id)
    ).astype("string")
    posts["source_account_id"] = posts["account_id"]
    posts["dataset_id"] = str(dataset_id)
    posts["issue_id"] = str(issue_id)
    posts["body_clean"] = (
        posts["text"].str.replace(r"https?://\S+", "", regex=True)
        .str.replace(r"@\w+", "", regex=True)
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
    )
    posts["text_model_input"] = posts["body_clean"].where(
        posts["body_clean"].str.len().gt(0), posts["text"]
    )
    posts["body_len"] = posts["body_clean"].str.len().astype(float)
    posts["n_tags"] = posts["text"].str.count(r"#[\w_]+")
    posts["has_url"] = posts["text"].str.contains(r"https?://", regex=True, na=False).astype(float)
    posts = posts.dropna(subset=["post_id", "account_id", "date"])
    posts = posts[posts["text_model_input"].str.strip().ne("")].copy()
    if posts.empty:
        raise ValueError("Tidak ada post valid: post_id, account_id, date, dan text wajib tersedia")
    if posts["post_id"].duplicated().any():
        posts = posts.drop_duplicates("post_id", keep="first")
    posts["account_key"] = posts.apply(
        lambda row: account_key(row["dataset_id"], row["account_id"]), axis=1
    )
    return posts.reset_index(drop=True)


def _encode_live_texts(texts: list[str], checkpoint: str, max_length: int = 128) -> np.ndarray:
    tokenizer, encoder = _load_text_encoder(checkpoint)
    embeddings: list[np.ndarray] = []
    with torch.no_grad():
        for start in range(0, len(texts), 32):
            encoded = tokenizer(
                texts[start : start + 32],
                padding=True,
                truncation=True,
                max_length=max_length,
                return_tensors="pt",
            )
            output = encoder(**encoded).last_hidden_state
            mask = encoded["attention_mask"].unsqueeze(-1).to(output.dtype)
            pooled = (output * mask).sum(dim=1) / mask.sum(dim=1).clamp_min(1.0)
            embeddings.append(pooled.cpu().numpy())
    return np.vstack(embeddings)


@lru_cache(maxsize=1)
def _load_text_encoder(checkpoint: str) -> tuple[Any, nn.Module]:
    tokenizer = AutoTokenizer.from_pretrained(checkpoint)
    encoder = AutoModel.from_pretrained(checkpoint)
    encoder.eval()
    for parameter in encoder.parameters():
        parameter.requires_grad = False
    return tokenizer, encoder


def _live_sequences(posts: pd.DataFrame, accounts: pd.DataFrame) -> dict[str, np.ndarray]:
    sequences: dict[str, np.ndarray] = {}
    ordered = posts.sort_values(["account_key", "date", "post_id"]).copy()
    ordered["n_tags_scaled"] = ordered["n_tags"].div(10.0).clip(0, 3)
    ordered["body_len_scaled"] = ordered["body_len"].div(280.0).clip(0, 4)
    ordered["has_url"] = ordered["has_url"].astype(float)
    ordered["is_reply"] = ordered["is_reply"].astype(float)
    ordered["is_quote"] = ordered["is_quote"].astype(float)
    hour = ordered["date"].dt.hour + ordered["date"].dt.minute / 60.0
    ordered["hour_sin"] = np.sin(2 * np.pi * hour / 24.0)
    ordered["hour_cos"] = np.cos(2 * np.pi * hour / 24.0)
    delta = ordered.groupby("account_key")["date"].diff().dt.total_seconds().div(3600).fillna(0)
    ordered["delta_hours_scaled"] = np.log1p(delta.clip(lower=0)).div(6.0).clip(0, 3)
    for key, group in ordered.groupby("account_key", sort=False):
        values = group[SEQUENCE_FEATURES].to_numpy(dtype=np.float32)
        if len(values):
            sequences[str(key)] = values
    missing = [key for key in accounts["account_key"] if key not in sequences]
    if missing:
        raise ValueError(f"Account live tanpa sequence: {missing[:5]}")
    return sequences


def _graph_inputs(accounts: pd.DataFrame, interactions: pd.DataFrame, checkpoint: dict[str, Any]) -> tuple[list[str], torch.Tensor, torch.Tensor, list[str]]:
    account_keys = set(accounts["account_key"].astype(str))
    edge_pairs: list[tuple[int, int]] = []
    target_keys: set[str] = set()
    for row in interactions.loc[interactions["is_valid_edge"], ["dataset_id", "source_account_id", "target_account_id"]].itertuples(index=False):
        source_key = account_key(row.dataset_id, row.source_account_id)
        target_key = account_key(row.dataset_id, row.target_account_id)
        account_keys.update({source_key, target_key})
        target_keys.add(target_key)
    node_order = sorted(account_keys)
    node_to_index = {key: index for index, key in enumerate(node_order)}
    feature_frame = accounts.set_index("account_key").reindex(node_order)
    numeric = feature_frame.reindex(columns=MODEL_FEATURES).apply(pd.to_numeric, errors="coerce").to_numpy(dtype=float)
    imputer = np.asarray(checkpoint["imputer_statistics"], dtype=float)
    scale = np.asarray(checkpoint["scaler_scale"], dtype=float)
    mean = np.asarray(checkpoint["scaler_mean"], dtype=float)
    if numeric.shape[1] != len(imputer):
        raise ValueError("Schema GraphSAGE live tidak cocok dengan checkpoint final")
    numeric = np.where(np.isnan(numeric), imputer, numeric)
    scale = np.where(np.abs(scale) < 1e-12, 1.0, scale)
    features = torch.tensor((numeric - mean) / scale, dtype=torch.float32)
    for row in interactions.loc[interactions["is_valid_edge"], ["dataset_id", "source_account_id", "target_account_id"]].itertuples(index=False):
        source = node_to_index[account_key(row.dataset_id, row.source_account_id)]
        target = node_to_index[account_key(row.dataset_id, row.target_account_id)]
        edge_pairs.extend([(source, target), (target, source)])
    edge_index = torch.tensor(edge_pairs, dtype=torch.long).t().contiguous() if edge_pairs else torch.empty((2, 0), dtype=torch.long)
    return node_order, features, edge_index, sorted(target_keys)


def _similarity_evidence(posts: pd.DataFrame) -> tuple[pd.Series, list[dict[str, Any]]]:
    values = posts["body_clean"].fillna("").astype(str)
    similarities = np.zeros(len(posts), dtype=float)
    phrases: list[dict[str, Any]] = []
    usable = values.str.strip().ne("")
    if usable.sum() < 2:
        return pd.Series(similarities, index=posts.index), phrases
    try:
        matrix = cosine_similarity(TfidfVectorizer(ngram_range=(1, 2), max_features=10000).fit_transform(values))
    except ValueError:
        return pd.Series(similarities, index=posts.index), phrases
    keys = posts["account_key"].to_numpy()
    for index in range(len(posts)):
        matrix[index, keys == keys[index]] = 0.0
        similarities[index] = float(matrix[index].max())
        peer = int(matrix[index].argmax())
        if similarities[index] >= 0.75 and len(phrases) < 20:
            phrases.append({
                "phrase": values.iloc[index][:160],
                "count": 2,
                "similarity": round(similarities[index] * 100, 1),
            })
    deduped: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in sorted(phrases, key=lambda value: value["similarity"], reverse=True):
        key = item["phrase"]
        if key not in seen:
            seen.add(key)
            deduped.append(item)
    return pd.Series(similarities, index=posts.index), deduped[:8]


def _status(value: float) -> str:
    return "danger" if value >= 70 else "warning" if value >= 40 else "normal"


class LiveModelEngine:
    """Load final artifacts once and score one live scrape at a time."""

    def __init__(self, root: str | Path):
        self.root = Path(root).resolve()
        model_dir = self.root / "models" / "final"
        with (model_dir / "indobertweet_final.pkl").open("rb") as handle:
            self.text_artifact = pickle.load(handle)
        self.temporal_artifact = torch.load(model_dir / "temporal_lstm_final.pt", map_location="cpu", weights_only=False)
        self.graph_artifact = torch.load(model_dir / "graphsage_final.pt", map_location="cpu", weights_only=False)

        self.text_checkpoint = self.text_artifact["encoder"].get("checkpoint", DEFAULT_CHECKPOINT)
        self.text_classifier = self.text_artifact["classifier"]
        self.temporal_model = TemporalLSTMClassifier(
            input_size=int(self.temporal_artifact["input_size"]),
            hidden_size=int(self.temporal_artifact["hidden_size"]),
        )
        self.temporal_model.load_state_dict(self.temporal_artifact["state_dict"])
        self.temporal_model.eval()
        self.graph_model = GraphSAGEClassifier(
            input_size=int(self.graph_artifact["input_size"]),
            hidden_size=int(self.graph_artifact["hidden_size"]),
        )
        self.graph_model.load_state_dict(self.graph_artifact["state_dict"])
        self.graph_model.eval()

    def predict(self, raw_posts: pd.DataFrame, query: str = "") -> dict[str, Any]:
        posts = prepare_live_posts(raw_posts, dataset_id="live", issue_id=query or "live")
        interactions, graph_frame, graph_stats = _build_graph(posts)
        accounts = _account_features(posts, graph_frame)
        accounts["account_key"] = accounts.apply(
            lambda row: account_key(row["dataset_id"], row["account_id"]), axis=1
        )
        accounts["follower_ratio_ui"] = accounts["following"] / accounts["followers"].clip(lower=1)

        text_frame = posts[["account_key", "text_model_input"]].rename(columns={"text_model_input": "text"})
        text_embeddings = _encode_live_texts(text_frame["text"].tolist(), self.text_checkpoint, int(self.text_artifact["encoder"].get("max_length", 128)))
        pooled = pool_post_embeddings(text_frame, text_embeddings, accounts["account_key"])
        text_probabilities = self.text_classifier.predict_proba(pooled)[:, 1]

        sequences = _live_sequences(posts, accounts)
        sequence_tensors = [torch.tensor(sequences[key], dtype=torch.float32) for key in accounts["account_key"]]
        with torch.no_grad():
            temporal_probabilities = torch.softmax(self.temporal_model(sequence_tensors), dim=1)[:, 1].numpy()

        node_order, graph_features, edge_index, _ = _graph_inputs(accounts, interactions, self.graph_artifact)
        with torch.no_grad():
            graph_probabilities = torch.softmax(self.graph_model(graph_features, edge_index)[0], dim=1)[:, 1].numpy()
        graph_by_key = dict(zip(node_order, graph_probabilities))
        graph_probabilities = np.asarray([graph_by_key.get(key, 0.0) for key in accounts["account_key"]])

        similarity, repeated_phrases = _similarity_evidence(posts)
        posts["duplicate_similarity"] = similarity.to_numpy()
        posts["burst_event"] = posts["date"].dt.floor("min").map(
            posts.groupby(posts["date"].dt.floor("min"))["account_key"].nunique() >= 3
        ).fillna(False)
        account_similarity = posts.groupby("account_key")["duplicate_similarity"].mean()
        fusion = (
            FUSION_WEIGHTS["indobertweet"] * text_probabilities
            + FUSION_WEIGHTS["temporal_lstm"] * temporal_probabilities
            + FUSION_WEIGHTS["graphsage"] * graph_probabilities
        )
        context_limited = len(posts) < 3 or len(accounts) < 2
        output_accounts: list[dict[str, Any]] = []
        for index, row in accounts.reset_index(drop=True).iterrows():
            probability = float(fusion[index])
            predicted = "Buzzer" if probability >= 0.65 else "Organic" if probability <= 0.35 else "Review"
            review_status = "MODEL_OUTPUT"
            if context_limited:
                predicted = "Review"
                review_status = "INSUFFICIENT_CONTEXT"
            username = str(row.get("username") or "unknown")
            account_posts = posts[posts["account_key"].eq(row["account_key"])].sort_values("date")
            age_days = max(1, int((pd.Timestamp.now(tz="UTC") - pd.to_datetime(row.get("created"), utc=True)).days)) if pd.notna(row.get("created")) else 1
            profile_score = min(100.0, (_safe_float(row.get("post_rate")) / 20.0) * 100.0)
            indicators = [
                {"name": "IndoBERTweet", "score": round(float(text_probabilities[index]) * 100, 1), "weight": 0.4, "description": "Sinyal kemiripan dan pola bahasa antar-postingan.", "status": _status(float(text_probabilities[index]) * 100)},
                {"name": "Temporal LSTM", "score": round(float(temporal_probabilities[index]) * 100, 1), "weight": 0.3, "description": "Sinyal urutan postingan dan interval waktu.", "status": _status(float(temporal_probabilities[index]) * 100)},
                {"name": "GraphSAGE", "score": round(float(graph_probabilities[index]) * 100, 1), "weight": 0.3, "description": "Sinyal struktur reply/quote dan komponen graf.", "status": _status(float(graph_probabilities[index]) * 100)},
                {"name": "Aktivitas Profil", "score": round(profile_score, 1), "weight": 0.0, "description": "Konteks aktivitas profil; bukan cabang model fusion.", "status": _status(profile_score)},
            ]
            evidence = []
            if _safe_float(account_similarity.get(row["account_key"], 0)) >= 0.75:
                evidence.append(f"kemiripan teks lintas akun {account_similarity[row['account_key']]:.2f}")
            if _safe_float(row.get("burst_ratio_1h")) >= 0.5:
                evidence.append(f"interval posting pendek ({_safe_float(row.get('burst_ratio_1h')):.2f})")
            if _safe_int(row.get("total_degree")) > 0:
                evidence.append(f"degree graf {int(row['total_degree'])}")
            if not evidence:
                evidence.append("belum ada bukti koordinasi dominan pada sampel")
            tweets = []
            for post in account_posts.head(5).itertuples():
                tweets.append({
                    "id": str(post.post_id),
                    "date": pd.Timestamp(post.date).isoformat(),
                    "text": str(post.text),
                    "relationType": str(post.relation_type),
                    "targetUsername": str(post.target_username) if pd.notna(post.target_username) else None,
                    "targetPostId": str(post.target_post_id) if pd.notna(post.target_post_id) else None,
                    "duplicateSimilarity": round(_safe_float(post.duplicate_similarity), 3),
                    "burstEvent": bool(post.burst_event),
                })
            output_accounts.append({
                "id": str(row["account_id"]),
                "username": username,
                "name": username,
                "avatar": str(row.get("avatar") or ""),
                "bio": str(row.get("bio") or ""),
                "created": pd.Timestamp(row["first_post"]).isoformat() if pd.notna(row.get("first_post")) else "",
                "accountAgeDays": age_days,
                "followers": _safe_int(row.get("followers")),
                "following": _safe_int(row.get("following")),
                "followerRatio": round(_safe_float(row.get("follower_ratio_ui")), 4),
                "statuses": _safe_int(row.get("statuses")),
                "statusesPerDay": round(_safe_float(row.get("statuses")) / age_days, 2),
                "buzzerScore": round(probability * 100, 2),
                "riskLevel": "high" if probability >= 0.65 else "low" if probability <= 0.35 else "medium",
                "campaignIssue": query or "live",
                "nPostsInDataset": _safe_int(row.get("n_posts")),
                "postRatePerHour": round(_safe_float(row.get("post_rate")), 4),
                "duplicateTextRatio": round(_safe_float(account_similarity.get(row["account_key"], 0)), 4),
                "burstRatio": round(_safe_float(row.get("burst_ratio_1h")), 4),
                "outDegree": _safe_int(row.get("out_degree")),
                "clusterId": f"live-component-{_safe_int(row.get('component_size'), 1)}",
                "indicators": indicators,
                "tweets": tweets,
                "probabilityBuzzer": round(probability, 6),
                "confidence": round(abs(probability - 0.5) * 2, 6),
                "prediction": predicted,
                "reviewStatus": review_status,
                "explanation": " | ".join(evidence),
                "branchScores": {"indobertweet": round(float(text_probabilities[index]), 6), "temporal_lstm": round(float(temporal_probabilities[index]), 6), "graphsage": round(float(graph_probabilities[index]), 6)},
            })

        output_accounts.sort(key=lambda value: value["buzzerScore"], reverse=True)
        summary = {
            "total_accounts": len(output_accounts),
            "total_posts": int(len(posts)),
            "high_risk_count": sum(value["riskLevel"] == "high" for value in output_accounts),
            "medium_risk_count": sum(value["riskLevel"] == "medium" for value in output_accounts),
            "low_risk_count": sum(value["riskLevel"] == "low" for value in output_accounts),
            "review_count": sum(value["prediction"] == "Review" for value in output_accounts),
            "average_score": round(float(np.mean(fusion) * 100), 2),
            "duplicate_ratio": round(float(posts["duplicate_similarity"].mean()), 4),
            "burst_ratio": round(float(accounts["burst_ratio_1h"].mean()), 4),
            "clusters_detected": int(graph_stats.get("graph_nodes", 0)),
        }
        return {
            "source": "live_scrape",
            "query": query,
            "modelVersion": MODEL_VERSION,
            "schemaVersion": SCHEMA_VERSION,
            "accounts": output_accounts,
            "summary": summary,
            "repeatedPhrases": repeated_phrases,
            "networkEdges": [
                {"source": str(row.source_account_id), "target": str(row.target_account_id), "relationType": str(row.relation_type)}
                for row in interactions.loc[interactions["is_valid_edge"], ["source_account_id", "target_account_id", "relation_type"]].itertuples()
            ],
            "warnings": [
                "Skor adalah indikasi koordinasi, bukan vonis bahwa akun adalah buzzer.",
                "Sampel live kecil diarahkan ke human review." if context_limited else "",
            ],
            "graph": graph_stats,
        }


def load_static_predictions(root: str | Path) -> dict[str, Any]:
    """Load the research-final contract for dashboard/offline inspection."""
    root_path = Path(root).resolve()
    path = root_path / "output" / "final_model" / "final_predictions.csv"
    if not path.exists():
        raise FileNotFoundError(f"Final predictions tidak ditemukan: {path}")
    frame = pd.read_csv(path, dtype="string", keep_default_na=True)
    return {"source": "final_contract", "modelVersion": MODEL_VERSION, "accounts": json.loads(frame.to_json(orient="records"))}
