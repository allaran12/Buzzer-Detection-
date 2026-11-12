#!/usr/bin/env python3
"""Generate the canonical Phase 3 feature schema from standardized data."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import networkx as nx
import numpy as np
import pandas as pd


BATCH_CONFIG = {
    "batch2": {"issue_id": "wowo2", "source": "data/processed/wowo2/standardized_data.csv"},
    "batch3": {"issue_id": "RoySuryo", "source": "data/processed/RoySuryo/standardized_data.csv"},
    "batch4": {"issue_id": "ManfaatnyaDirasakan", "source": "data/processed/ManfaatnyaDirasakan/standardized_data.csv"},
    "batch5": {"issue_id": "rasanyaman", "source": "data/processed/rasanyaman/standardized_data.csv"},
    "batch6": {"issue_id": "misi18tokped", "source": "data/processed/misi18tokped/standardized_data.csv"},
}
ID_COLUMNS = [
    "post_id", "account_id", "id", "user_id", "source_post_id",
    "source_account_id", "target_post_id", "target_account_id",
    "conversation_id",
]
TEMPORAL_FEATURES = [
    "sequence_len", "mean_interval_hours", "std_interval_hours",
    "min_interval_hours", "max_interval_hours", "burst_ratio_1h",
    "active_span_hours_observed", "active_days_observed", "hour_entropy",
]
GRAPH_FEATURES = [
    "in_degree", "out_degree", "total_degree", "pagerank", "component_size",
    "graph_in_degree", "graph_out_degree", "graph_unique_targets",
    "graph_unique_sources", "graph_pagerank", "graph_component_size",
]
CANONICAL_ACCOUNT_COLUMNS = [
    "account_id", "username", "dataset_id", "issue_id", "n_posts",
    "avg_tags", "avg_body_len", "url_rate", "avg_words", "n_replies",
    "n_quotes", "n_originals", "first_post", "last_post", "followers",
    "following", "follower_ratio", "active_hours", "post_rate",
    *TEMPORAL_FEATURES, *GRAPH_FEATURES, "text_blob",
]
LABEL_METADATA_COLUMNS = [
    "label", "evidence", "notes", "review_status", "candidate_type",
    "label_source",
]


def repo_root(path: str | Path | None = None) -> Path:
    if path is not None:
        root = Path(path).resolve()
    else:
        root = Path.cwd().resolve()
        while root != root.parent and not (root / "PRD.md").exists():
            root = root.parent
    if not (root / "PRD.md").exists():
        raise FileNotFoundError("Repository root dengan PRD.md tidak ditemukan")
    return root


def normalize_id(value: Any) -> str | pd._libs.missing.NAType:
    if value is None or pd.isna(value):
        return pd.NA
    text = str(value).strip()
    if not text or text.lower() in {"nan", "none", "<na>"}:
        return pd.NA
    if re.search(r"[eE][+-]?\d+", text):
        return pd.NA
    if text.endswith(".0") and text[:-2].isdigit():
        text = text[:-2]
    return text


def username_key(value: Any) -> str | None:
    if value is None or pd.isna(value):
        return None
    text = str(value).strip()
    return text.lower() if text else None


def _series(frame: pd.DataFrame, column: str, default: Any = pd.NA) -> pd.Series:
    if column in frame.columns:
        return frame[column]
    return pd.Series(default, index=frame.index)


def _first_non_null(values: pd.Series) -> Any:
    non_null = values.dropna()
    return non_null.iloc[0] if not non_null.empty else pd.NA


def _entropy(values: pd.Series) -> float:
    counts = values.value_counts(normalize=True)
    return float(-(counts * np.log2(counts)).sum()) if not counts.empty else 0.0


def _minmax(values: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(values, errors="coerce").fillna(0.0)
    clipped = numeric.clip(upper=numeric.quantile(0.95))
    span = float(clipped.max() - clipped.min())
    return (clipped - clipped.min()) / span if span > 0 else pd.Series(0.0, index=values.index)


def _parse_candidate_type(root: Path, batch: str) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for suffix, candidate_type in (("top30_for_review", "Top30_Suspicious"), ("random20_for_review", "Random20_Baseline")):
        path = root / "data" / "labels" / f"{batch}_{suffix}.csv"
        if not path.exists():
            continue
        frame = pd.read_csv(path, dtype="string")
        if "username" not in frame:
            continue
        for value in frame["username"].dropna():
            mapping[username_key(value)] = candidate_type
    return mapping


def _load_labels(root: Path, batch: str, accounts: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    path = root / "data" / "labels" / f"{batch}_labeled_combined.csv"
    if not path.exists():
        empty = pd.DataFrame(columns=[
            "account_id", "username", "dataset_id", "issue_id", "label", "evidence",
            "notes", "review_status", "candidate_type", "label_source",
        ])
        return empty, {
            "source_path": None,
            "source_rows": 0,
            "label_counts": {},
            "unmatched_labels": 0,
            "status": "NO_MANUAL_LABELS",
        }
    labels = pd.read_csv(path, dtype="string", keep_default_na=True)
    if "username" not in labels.columns or "label" not in labels.columns:
        raise ValueError(f"Label {path} harus memiliki username dan label")
    labels["username_key"] = labels["username"].map(username_key)
    if labels["username_key"].duplicated().any():
        raise ValueError(f"Duplicate username pada label {batch}")
    labels["label"] = pd.to_numeric(labels["label"], errors="coerce").astype("Int64")
    labels = labels.dropna(subset=["username_key", "label"]).copy()
    labels["label"] = labels["label"].astype(int)
    if not set(labels["label"].unique()).issubset({0, 1}):
        raise ValueError(f"Label {batch} harus 0/1")

    account_lookup = (
        accounts.assign(username_key=accounts["username"].map(username_key))
        .drop_duplicates("username_key")
        .set_index("username_key")
    )
    candidate_types = _parse_candidate_type(root, batch)
    labels["account_id"] = labels["username_key"].map(account_lookup["account_id"])
    labels["dataset_id"] = batch
    labels["issue_id"] = BATCH_CONFIG[batch]["issue_id"]
    labels["evidence"] = _series(labels, "evidence") if "evidence" in labels else _series(labels, "notes")
    if "evidence" not in labels.columns:
        labels["evidence"] = labels["notes"]
    labels["evidence"] = labels["evidence"].replace(r"^\s*$", pd.NA, regex=True)
    labels["notes"] = _series(labels, "notes")
    labels["notes"] = labels["notes"].replace(r"^\s*$", pd.NA, regex=True)
    labels["review_status"] = _series(labels, "review_status")
    labels["review_status"] = labels["review_status"].fillna("LEGACY_MANUAL_LABEL")
    labels["candidate_type"] = _series(labels, "candidate_type")
    labels["candidate_type"] = labels["candidate_type"].fillna(labels["username_key"].map(candidate_types))
    labels["candidate_type"] = labels["candidate_type"].fillna("LABELED_COMBINED")
    labels["label_source"] = path.name

    canonical = labels[
        ["account_id", "username", "dataset_id", "issue_id", "label", "evidence",
         "notes", "review_status", "candidate_type", "label_source"]
    ].copy()
    canonical["account_id"] = canonical["account_id"].map(normalize_id).astype("string")
    unmatched = int(canonical["account_id"].isna().sum())
    stats = {
        "source_path": str(path),
        "source_rows": int(len(labels)),
        "label_counts": {str(k): int(v) for k, v in labels["label"].value_counts().sort_index().items()},
        "unmatched_labels": unmatched,
    }
    return canonical, stats


def _prepare_posts(root: Path, batch: str) -> tuple[pd.DataFrame, dict[str, Any]]:
    config = BATCH_CONFIG[batch]
    source_path = root / config["source"]
    if not source_path.exists():
        raise FileNotFoundError(f"Standardized source tidak ditemukan: {source_path}")
    posts = pd.read_csv(source_path, dtype="string", keep_default_na=True)
    source_rows = len(posts)
    for column in ID_COLUMNS:
        if column in posts.columns:
            posts[column] = posts[column].map(normalize_id).astype("string")
    posts["account_id"] = posts["account_id"].map(normalize_id).astype("string")
    posts["source_account_id"] = _series(posts, "source_account_id", pd.NA).map(normalize_id).astype("string")
    posts["source_account_id"] = posts["source_account_id"].fillna(posts["account_id"])
    posts["target_account_id"] = _series(posts, "target_account_id", pd.NA).map(normalize_id).astype("string")
    posts["username"] = _series(posts, "username", pd.NA).astype("string").str.strip()
    posts["target_username"] = _series(posts, "target_username", pd.NA).astype("string").str.strip()
    posts["post_id"] = posts["post_id"].map(normalize_id).astype("string")
    posts["relation_type"] = _series(posts, "relation_type", "original").fillna("original").astype("string").str.lower().str.strip()
    posts["text"] = _series(posts, "text", "").fillna("").astype("string")
    posts["date"] = pd.to_datetime(_series(posts, "date"), errors="coerce", utc=True)
    posts["dataset_id"] = batch
    posts["issue_id"] = config["issue_id"]

    username_to_id: dict[str, str] = {}
    conflicts: set[str] = set()
    for username, account_id in posts[["username", "account_id"]].dropna().itertuples(index=False):
        key = username_key(username)
        value = normalize_id(account_id)
        if key is None or pd.isna(value):
            continue
        previous = username_to_id.get(key)
        if previous is not None and previous != value:
            conflicts.add(key)
        username_to_id[key] = value
    if conflicts:
        raise ValueError(f"Username memetakan lebih dari satu account_id pada {batch}: {sorted(conflicts)[:5]}")

    raw_target = posts["target_account_id"].copy()
    posts["target_account_id"] = posts["target_account_id"].fillna(
        posts["target_username"].map(username_to_id)
    ).astype("string")

    posts["hashtags"] = posts["text"].str.findall(r"#[\w_]+", flags=re.UNICODE).map(
        lambda values: json.dumps(values, ensure_ascii=False)
    ).astype("string")
    posts["n_tags"] = posts["text"].str.count(r"#[\w_]+")
    posts["body_clean"] = (
        posts["text"].str.replace(r"https?://\S+", "", regex=True)
        .str.replace(r"@\w+", "", regex=True)
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
    )
    posts["body_len"] = posts["body_clean"].str.len().astype("int64")
    posts["has_url"] = posts["text"].str.contains(r"https?://", regex=True, na=False).astype("int64")
    posts["text_model_input"] = posts["body_clean"]
    posts["date_only"] = posts["date"].dt.strftime("%Y-%m-%d")

    duplicate_posts = int(posts["post_id"].duplicated().sum())
    missing_posts = int(posts["post_id"].isna().sum())
    missing_accounts = int(posts["account_id"].isna().sum())
    if duplicate_posts or missing_posts or missing_accounts:
        raise ValueError(
            f"Standardized {batch} tidak valid: duplicate_post_id={duplicate_posts}, "
            f"missing_post_id={missing_posts}, missing_account_id={missing_accounts}"
        )

    interaction_mask = posts["relation_type"].isin(["reply", "quote"])
    target_missing_before = int(raw_target.loc[interaction_mask].isna().sum())
    target_missing_after = int(posts.loc[interaction_mask, "target_account_id"].isna().sum())
    stats = {
        "source_path": str(source_path),
        "source_rows": int(source_rows),
        "posts": int(len(posts)),
        "unique_posts": int(posts["post_id"].nunique()),
        "accounts": int(posts["account_id"].nunique()),
        "invalid_dates": int(posts["date"].isna().sum()),
        "duplicate_posts": duplicate_posts,
        "relation_counts": {str(k): int(v) for k, v in posts["relation_type"].value_counts().sort_index().items()},
        "interaction_rows": int(interaction_mask.sum()),
        "target_missing_before_username_resolution": target_missing_before,
        "target_unresolved_after_username_resolution": target_missing_after,
        "invalid_target_ids_before_resolution": int((raw_target.notna() & posts["target_account_id"].isna()).sum()),
    }
    return posts, stats


def _build_graph(posts: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    interaction_mask = posts["relation_type"].isin(["reply", "quote"])
    interactions = posts.loc[interaction_mask, [
        "post_id", "dataset_id", "issue_id", "date", "username", "source_account_id",
        "target_account_id", "target_username", "relation_type",
    ]].copy()
    interactions = interactions.rename(columns={"source_account_id": "source_account_id"})
    interactions["edge_id"] = interactions["dataset_id"].astype(str) + ":" + interactions["post_id"].astype(str)
    interactions["is_self_loop"] = interactions["source_account_id"] == interactions["target_account_id"]
    interactions["is_valid_edge"] = (
        interactions["source_account_id"].notna()
        & interactions["target_account_id"].notna()
        & ~interactions["is_self_loop"]
    )
    valid = interactions[interactions["is_valid_edge"]].copy()

    graph = nx.DiGraph()
    graph.add_nodes_from(posts["account_id"].dropna().astype(str).unique())
    graph.add_edges_from(valid[["source_account_id", "target_account_id"]].astype(str).itertuples(index=False, name=None))
    pagerank = nx.pagerank(graph, alpha=0.85) if graph.number_of_nodes() else {}
    undirected = graph.to_undirected()
    component_sizes: dict[str, int] = {}
    for component in nx.connected_components(undirected):
        for node in component:
            component_sizes[str(node)] = len(component)

    rows = []
    for account_id in posts["account_id"].dropna().astype(str).drop_duplicates():
        rows.append({
            "account_id": account_id,
            "in_degree": int(graph.in_degree(account_id)) if account_id in graph else 0,
            "out_degree": int(graph.out_degree(account_id)) if account_id in graph else 0,
            "total_degree": int(graph.degree(account_id)) if account_id in graph else 0,
            "pagerank": float(pagerank.get(account_id, 0.0)),
            "component_size": int(component_sizes.get(account_id, 1)),
            "graph_in_degree": int(graph.in_degree(account_id)) if account_id in graph else 0,
            "graph_out_degree": int(graph.out_degree(account_id)) if account_id in graph else 0,
            "graph_unique_targets": int(len(set(graph.successors(account_id)))) if account_id in graph else 0,
            "graph_unique_sources": int(len(set(graph.predecessors(account_id)))) if account_id in graph else 0,
            "graph_pagerank": float(pagerank.get(account_id, 0.0)),
            "graph_component_size": int(component_sizes.get(account_id, 1)),
        })
    graph_frame = pd.DataFrame(rows)
    stats = {
        "interaction_rows": int(len(interactions)),
        "valid_edge_events": int(len(valid)),
        "unresolved_edge_events": int((~interactions["is_valid_edge"]).sum()),
        "self_loop_events_removed": int(interactions["is_self_loop"].sum()),
        "unique_directed_edges": int(valid[["source_account_id", "target_account_id"]].drop_duplicates().shape[0]),
        "graph_nodes": int(graph.number_of_nodes()),
        "graph_edges": int(graph.number_of_edges()),
    }
    return interactions, graph_frame, stats


def _account_features(posts: pd.DataFrame, graph_frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for account_id, group in posts.groupby("account_id", dropna=True, sort=False):
        group = group.sort_values("date")
        times = group["date"].dropna()
        intervals = times.diff().dt.total_seconds().div(3600).dropna()
        active_hours = float((times.max() - times.min()).total_seconds() / 3600) if len(times) > 1 else 0.0
        rows.append({
            "account_id": str(account_id),
            "username": _first_non_null(group["username"]),
            "dataset_id": _first_non_null(group["dataset_id"]),
            "issue_id": _first_non_null(group["issue_id"]),
            "n_posts": int(len(group)),
            "avg_tags": float(group["n_tags"].mean()),
            "avg_body_len": float(group["body_len"].mean()),
            "url_rate": float(group["has_url"].mean()),
            "avg_words": float(group["body_clean"].str.split().str.len().mean()),
            "n_replies": int((group["relation_type"] == "reply").sum()),
            "n_quotes": int((group["relation_type"] == "quote").sum()),
            "n_originals": int((group["relation_type"] == "original").sum()),
            "first_post": times.min() if not times.empty else pd.NaT,
            "last_post": times.max() if not times.empty else pd.NaT,
            "followers": _first_non_null(pd.to_numeric(group.get("followers"), errors="coerce")),
            "following": _first_non_null(pd.to_numeric(group.get("following"), errors="coerce")),
            "follower_ratio": np.nan,
            "active_hours": active_hours,
            "post_rate": 10.0 if active_hours <= 0 else float(len(group) / active_hours),
            "sequence_len": int(len(group)),
            "mean_interval_hours": float(intervals.mean()) if not intervals.empty else np.nan,
            "std_interval_hours": float(intervals.std(ddof=0)) if not intervals.empty else np.nan,
            "min_interval_hours": float(intervals.min()) if not intervals.empty else np.nan,
            "max_interval_hours": float(intervals.max()) if not intervals.empty else np.nan,
            "burst_ratio_1h": float((intervals <= 1).mean()) if not intervals.empty else 0.0,
            "active_span_hours_observed": active_hours,
            "active_days_observed": int(times.dt.date.nunique()) if not times.empty else 0,
            "hour_entropy": _entropy(times.dt.hour) if not times.empty else 0.0,
            "text_blob": " ".join(group["body_clean"].fillna("").astype(str)).strip(),
        })
    accounts = pd.DataFrame(rows)
    accounts["follower_ratio"] = accounts["followers"] / (accounts["following"] + 1)
    accounts = accounts.merge(graph_frame, on="account_id", how="left")
    for column in GRAPH_FEATURES:
        accounts[column] = pd.to_numeric(accounts[column], errors="coerce").fillna(0)
    return accounts


def _add_scores(accounts: pd.DataFrame) -> pd.DataFrame:
    accounts = accounts.copy()
    accounts["score_post_rate"] = _minmax(accounts["post_rate"])
    accounts["score_high_tags"] = _minmax(accounts["avg_tags"])
    accounts["score_body_length"] = _minmax(accounts["avg_body_len"])
    accounts["score_out_degree"] = _minmax(accounts["out_degree"])
    accounts["score_low_follower_ratio"] = 1 - _minmax(accounts["follower_ratio"])
    accounts["buzzer_score"] = (
        0.25 * accounts["score_post_rate"]
        + 0.20 * accounts["score_high_tags"]
        + 0.15 * accounts["score_body_length"]
        + 0.25 * accounts["score_out_degree"]
        + 0.15 * accounts["score_low_follower_ratio"]
    ).round(6)
    return accounts


def generate_batch(root: str | Path, batch: str) -> dict[str, Any]:
    root_path = repo_root(root)
    if batch not in BATCH_CONFIG:
        raise ValueError(f"Batch tidak dikenal: {batch}")
    posts, post_stats = _prepare_posts(root_path, batch)
    interactions, graph_frame, graph_stats = _build_graph(posts)
    accounts = _account_features(posts, graph_frame)
    accounts = _add_scores(accounts)
    labels, label_stats = _load_labels(root_path, batch, accounts)

    account_with_scores = accounts.merge(labels, on=["account_id", "username", "dataset_id", "issue_id"], how="left")
    account_with_scores["label"] = pd.to_numeric(account_with_scores["label"], errors="coerce").astype("Int64")
    for column in LABEL_METADATA_COLUMNS:
        if column not in account_with_scores:
            account_with_scores[column] = pd.NA
    account_with_scores = account_with_scores[
        [*CANONICAL_ACCOUNT_COLUMNS, "score_post_rate", "score_high_tags", "score_body_length",
         "score_out_degree", "score_low_follower_ratio", "buzzer_score", *LABEL_METADATA_COLUMNS]
    ]
    labels = labels.sort_values("username").reset_index(drop=True)

    output_dir = root_path / "data" / "features"
    labels_dir = root_path / "data" / "labels"
    output_dir.mkdir(parents=True, exist_ok=True)
    labels_dir.mkdir(parents=True, exist_ok=True)
    posts_path = output_dir / f"{batch}_posts_with_features.csv"
    accounts_path = output_dir / f"{batch}_account_features.csv"
    scored_path = output_dir / f"{batch}_account_features_with_scores.csv"
    interactions_path = output_dir / f"{batch}_interactions.csv"
    labels_path = labels_dir / f"{batch}_labeled_canonical.csv"
    validation_path = output_dir / f"{batch}_validation.json"

    posts.to_csv(posts_path, index=False, encoding="utf-8-sig", date_format="%Y-%m-%dT%H:%M:%SZ")
    accounts[CANONICAL_ACCOUNT_COLUMNS].to_csv(accounts_path, index=False, encoding="utf-8-sig", date_format="%Y-%m-%dT%H:%M:%SZ")
    account_with_scores.to_csv(scored_path, index=False, encoding="utf-8-sig", date_format="%Y-%m-%dT%H:%M:%SZ")
    interactions.to_csv(interactions_path, index=False, encoding="utf-8-sig", date_format="%Y-%m-%dT%H:%M:%SZ")
    labels.to_csv(labels_path, index=False, encoding="utf-8-sig")

    validation = {
        "schema_version": "canonical-v1",
        "batch": batch,
        "issue_id": BATCH_CONFIG[batch]["issue_id"],
        "post": post_stats,
        "graph": graph_stats,
        "labels": label_stats,
        "account_features": {
            "rows": int(len(accounts)),
            "unique_account_ids": int(accounts["account_id"].nunique()),
            "missing_account_ids": int(accounts["account_id"].isna().sum()),
            "columns": list(accounts.columns),
        },
        "label_preservation": {
            "source_counts": label_stats["label_counts"],
            "canonical_counts": {str(k): int(v) for k, v in labels["label"].value_counts().sort_index().items()},
        },
        "artifacts": {
            "posts": str(posts_path),
            "accounts": str(accounts_path),
            "accounts_with_scores": str(scored_path),
            "interactions": str(interactions_path),
            "labels": str(labels_path),
        },
    }
    validation_path.write_text(json.dumps(validation, indent=2, default=str), encoding="utf-8")
    return validation


def generate_all(root: str | Path | None = None) -> dict[str, Any]:
    root_path = repo_root(root)
    return {batch: generate_batch(root_path, batch) for batch in BATCH_CONFIG}


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate canonical CoordinX Phase 3 features")
    parser.add_argument("--root", default=None)
    parser.add_argument("--batch", choices=[*BATCH_CONFIG.keys(), "all"], default="all")
    args = parser.parse_args()
    result = generate_all(args.root) if args.batch == "all" else {args.batch: generate_batch(args.root, args.batch)}
    for batch, validation in result.items():
        print(
            f"{batch}: posts={validation['post']['posts']}, accounts={validation['account_features']['rows']}, "
            f"edge_events={validation['graph']['valid_edge_events']}, "
            f"unique_edges={validation['graph']['unique_directed_edges']}"
        )


if __name__ == "__main__":
    main()
