from __future__ import annotations

import asyncio
import os
from pathlib import Path

import pandas as pd

from src.features.canonical_features import _account_features, _build_graph
from src.screpping import _scrape, ensure_compatible_columns, scrape_async


async def scrape_to_features(query: str, limit: int, cookies: str = "", fetch_replies: bool = True, days: int | None = None) -> pd.DataFrame:
    timeout_seconds = float(os.getenv("COORDINX_SCRAPE_TIMEOUT_SECONDS", "45"))
    try:
        posts = await asyncio.wait_for(
            scrape_async(query, limit=min(limit, 50), cookies=cookies, fetch_replies=fetch_replies, days=days),
            timeout=timeout_seconds,
        )
    except asyncio.TimeoutError as exc:
        raise RuntimeError(f"Scraping X timeout setelah {timeout_seconds:.0f} detik; coba limit lebih kecil atau akun/session lain") from exc
    posts = ensure_compatible_columns(posts)
    posts["post_id"] = posts["post_id"].astype("string")
    posts["account_id"] = posts["account_id"].astype("string")
    posts["source_account_id"] = posts["account_id"]
    posts["relation_type"] = "original"
    posts.loc[posts["is_reply"], "relation_type"] = "reply"
    posts.loc[posts["is_quote"], "relation_type"] = "quote"
    posts["source_post_id"] = posts["post_id"]
    posts["target_post_id"] = posts.get("target_post_id", pd.Series(index=posts.index, dtype="string"))
    posts["target_account_id"] = posts.get("target_account_id", pd.Series(index=posts.index, dtype="string"))
    posts["target_username"] = posts.get("target_username", pd.Series(index=posts.index, dtype="string"))
    posts["date"] = pd.to_datetime(posts["date"], utc=True, errors="coerce")
    posts["dataset_id"] = "live"
    posts["issue_id"] = query[:80]
    posts["n_tags"] = posts["text"].str.count(r"#[\w_]+")
    posts["body_clean"] = posts["text"].str.replace(r"https?://\S+", "", regex=True).str.replace(r"\s+", " ", regex=True).str.strip()
    posts["body_len"] = posts["body_clean"].str.len()
    posts["has_url"] = posts["text"].str.contains(r"https?://", regex=True, na=False).astype(int)
    posts["text_model_input"] = posts["body_clean"]
    _, graph_frame, _ = _build_graph(posts)
    return _account_features(posts, graph_frame)
