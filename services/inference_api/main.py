from __future__ import annotations

import asyncio
import os
import re
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING, Any
from urllib.parse import parse_qs, unquote, urlparse

import pandas as pd
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

from services.inference_api.account_manager import ScraperAccountManager, scraper_db_path
from src.inference.model_adapter import ModelAdapter
from src.inference.model_registry import get_model_config
from src.screpping import accounts_status_async, configure_session_async, scrape_async

if TYPE_CHECKING:
    from src.inference.live_model_inference import LiveModelEngine


class AccountCredentials(BaseModel):
    username: str = ""
    password: str = ""
    email: str = ""
    email_password: str = ""
    auth_token: str = ""
    ct0: str = ""


class AnalyzeRequest(BaseModel):
    model_config = {"extra": "forbid"}
    dataset_path: str | None = None
    model_experiment: str | None = None
    query: str | None = None
    limit: int = Field(default=25, ge=1, le=500)
    fetch_replies: bool = False
    days: int | None = Field(default=30, ge=1, le=365)


root = Path(__file__).resolve().parents[2]
account_manager = ScraperAccountManager(scraper_db_path(root))
model_adapter = ModelAdapter(get_model_config(root))
app = FastAPI(title="CoordinX Inference API", version="2.0.0")

LOCAL_DATASET_ALIASES = {
    "roysuryo": "RoySuryo.csv",
    "prayforkalimantan": "prayforkalimantan.csv",
    "wowo2": "wowo2.csv",
    "jokowi": "jokowi.csv",
    "riaricis": "riaricis.csv",
    "wowo": "wowo.csv",
}


def require_admin(token: str | None) -> None:
    expected = os.getenv("COORDINX_ADMIN_TOKEN")
    environment = os.getenv("COORDINX_ENV", "development").lower()
    if not expected and environment != "production":
        expected = "nexantara"
    if not expected or token != expected:
        raise HTTPException(status_code=401, detail="Admin token tidak valid")


@lru_cache(maxsize=1)
def get_engine() -> LiveModelEngine:
    from src.inference.live_model_inference import LiveModelEngine

    return LiveModelEngine(root)


def _safe_dataset_path(value: str) -> Path:
    candidate = Path(value)
    if not candidate.is_absolute():
        candidate = root / candidate
    resolved = candidate.resolve()
    allowed_roots = ((root / "data").resolve(), (root / "output").resolve())
    if not any(resolved == allowed or allowed in resolved.parents for allowed in allowed_roots):
        raise HTTPException(status_code=400, detail="dataset_path berada di luar direktori data/output yang diizinkan")
    if not resolved.is_file():
        raise HTTPException(status_code=404, detail=f"Dataset tidak ditemukan: {value}")
    return resolved


def _query_text(value: str) -> str:
    """Extract searchable text from plain queries and supported X URLs."""
    query = value.strip()
    parsed = urlparse(query)
    if not parsed.scheme or not parsed.netloc:
        return query
    path = parsed.path.strip("/")
    if path.lower().startswith("hashtag/"):
        return unquote(path.split("/", 1)[1])
    if path.lower() == "search":
        return unquote(parse_qs(parsed.query).get("q", [""])[0])
    return ""


def _local_dataset_for_query(query: str) -> Path | None:
    """Resolve a known offline sample without guessing for unrelated queries."""
    status_match = re.search(r"/status/(\d+)", query)
    if status_match:
        post_id = status_match.group(1)
        for candidate in sorted((root / "data" / "raw").glob("*.csv")):
            try:
                ids = pd.read_csv(candidate, dtype="string", usecols=["post_id"])["post_id"]
            except (OSError, ValueError, KeyError):
                continue
            if ids.eq(post_id).any():
                return candidate
        status_url = re.match(r"https?://[^/]+/([^/]+)/status/\d+", query, re.IGNORECASE)
        if status_url:
            username = unquote(status_url.group(1)).lstrip("@").casefold()
            matches: list[tuple[int, int, Path]] = []
            for candidate in sorted((root / "data" / "raw").glob("*.csv")):
                try:
                    users = pd.read_csv(candidate, dtype="string", usecols=["username"])["username"]
                except (OSError, ValueError, KeyError):
                    continue
                count = int(users.fillna("").str.casefold().eq(username).sum())
                if count:
                    matches.append((count, len(users), candidate))
            if matches:
                return max(matches, key=lambda item: (item[0], item[1]))[2]

    search_text = _query_text(query).lower()
    if not search_text:
        return None
    compact = re.sub(r"[^a-z0-9]+", "", search_text)
    for alias, filename in LOCAL_DATASET_ALIASES.items():
        if alias in compact:
            candidate = root / "data" / "raw" / filename
            if candidate.is_file():
                return candidate
    return None


async def _local_dataset_fallback(query: str, limit: int, reason: str) -> dict[str, Any] | None:
    """Keep the dashboard useful when X blocks the local twscrape session."""
    dataset_path = _local_dataset_for_query(query)
    if dataset_path is None:
        return None
    frame = await run_in_threadpool(pd.read_csv, dataset_path, dtype="string", keep_default_na=True)
    if "date" in frame.columns:
        parsed_dates = pd.to_datetime(frame["date"], errors="coerce", utc=True)
        frame = frame.assign(_sort_date=parsed_dates).sort_values(
            "_sort_date", ascending=False, na_position="last"
        ).drop(columns="_sort_date")
    frame = frame.head(limit).reset_index(drop=True)
    result = await run_in_threadpool(get_engine().predict, frame, query)
    result["source"] = "local_dataset_fallback"
    result["query"] = query
    result["fallback"] = {
        "dataset": str(dataset_path.relative_to(root)),
        "reason": reason,
        "liveScrapeAttempted": True,
    }
    result["warnings"] = [
        *result.get("warnings", []),
        "Scraping live X tidak tersedia pada sesi ini; hasil memakai sampel lokal yang relevan.",
        f"Dataset fallback: {dataset_path.relative_to(root)} ({len(frame)} postingan terbaru).",
    ]
    return result


def _catalog_value(row: dict[str, Any], key: str, default: Any = "") -> Any:
    value = row.get(key, default)
    if value is None:
        return default
    try:
        if bool(pd.isna(value)):
            return default
    except (TypeError, ValueError):
        pass
    return value


def _catalog_float(row: dict[str, Any], key: str, default: float = 0.0) -> float:
    value = _catalog_value(row, key, default)
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _catalog_int(row: dict[str, Any], key: str, default: int = 0) -> int:
    return int(_catalog_float(row, key, default))


def _profile_metadata() -> dict[tuple[str, str], dict[str, Any]]:
    """Read public profile fields from canonical post features for offline rows."""
    profiles: dict[tuple[str, str], dict[str, Any]] = {}
    columns = [
        "account_id",
        "dataset_id",
        "username",
        "name",
        "created",
        "followers",
        "following",
        "statuses",
        "n_posts",
        "post_rate",
        "burst_ratio_1h",
        "out_degree",
        "component_size",
        "bio",
        "avatar",
    ]
    for dataset_id in ("batch2", "batch3"):
        path = root / "data" / "features" / f"{dataset_id}_posts_with_features.csv"
        if not path.exists():
            continue
        available = pd.read_csv(path, nrows=0).columns.tolist()
        use_columns = [column for column in columns if column in available]
        if "account_id" not in use_columns:
            continue
        frame = pd.read_csv(path, dtype="string", usecols=use_columns)
        for row in frame.to_dict("records"):
            account_id = _catalog_value(row, "account_id")
            if not account_id:
                continue
            key = (str(_catalog_value(row, "dataset_id", dataset_id)), str(account_id))
            profile = profiles.setdefault(key, dict(row))
            profile["n_posts"] = _catalog_int(profile, "n_posts") + 1
    return profiles


def _catalog_frame() -> tuple[pd.DataFrame, str]:
    candidates = (
        (root / "output" / "final_model" / "final_predictions.csv", "final_contract"),
        (root / "output" / "phase7" / "phase7_predictions.csv", "phase7_contract"),
        (root / "data" / "predictions" / "phase7_combined_predictions.csv", "phase7_contract"),
    )
    for path, source in candidates:
        if path.exists():
            return pd.read_csv(path, dtype="string", keep_default_na=True), source
    return pd.DataFrame(), "final_contract"


def _catalog_account(row: dict[str, Any]) -> dict[str, Any]:
    probability = _catalog_float(row, "probability_buzzer")
    username = str(_catalog_value(row, "username", "unknown"))
    post_count = _catalog_int(row, "n_posts")
    statuses = _catalog_int(row, "statuses", post_count)
    avatar = str(_catalog_value(row, "avatar")).replace("_normal.", "_400x400.")
    created = str(_catalog_value(row, "created", _catalog_value(row, "first_post")))
    try:
        parsed_created = pd.to_datetime(created, utc=True, errors="coerce")
        account_age_days = max(1, int((pd.Timestamp.now(tz="UTC") - parsed_created).days)) if pd.notna(parsed_created) else 0
    except (TypeError, ValueError):
        account_age_days = 0
    followers = _catalog_int(row, "followers")
    following = _catalog_int(row, "following")
    follower_ratio = following / max(followers, 1) if followers else 0.0
    return {
        "id": str(_catalog_value(row, "account_id", username)),
        "username": username,
        "name": str(_catalog_value(row, "name", username)),
        "avatar": avatar,
        "bio": str(_catalog_value(row, "bio")),
        "created": created,
        "accountAgeDays": account_age_days,
        "followers": followers,
        "following": following,
        "followerRatio": round(follower_ratio, 4),
        "statuses": statuses,
        "statusesPerDay": round(statuses / account_age_days, 2) if account_age_days else 0,
        "buzzerScore": round(probability * 100, 2),
        "riskLevel": "high" if probability >= 0.65 else "low" if probability <= 0.35 else "medium",
        "campaignIssue": str(_catalog_value(row, "issue_id", _catalog_value(row, "dataset_id"))),
        "nPostsInDataset": post_count,
        "postRatePerHour": _catalog_float(row, "post_rate"),
        "duplicateTextRatio": _catalog_float(row, "max_peer_similarity", _catalog_float(row, "text_similarity_score")),
        "burstRatio": _catalog_float(row, "burst_ratio_1h"),
        "outDegree": _catalog_int(row, "out_degree"),
        "clusterId": str(_catalog_value(row, "component_size")),
        "indicators": [],
        "tweets": [],
        "prediction": str(_catalog_value(row, "prediction", "Review")),
        "confidence": round(abs(probability - 0.5) * 2, 4),
    }


def _empty_analysis_contract(
    *,
    source: str,
    query: str | None = None,
    model_version: str = "coordinx-final-v1.0.0",
    warning: str | None = None,
) -> dict[str, Any]:
    """Keep offline/model-only responses compatible with the live dashboard."""
    return {
        "source": source,
        "query": query,
        "modelVersion": model_version,
        "schemaVersion": "coordinx-final-output-v1",
        "accounts": [],
        "summary": {
            "total_accounts": 0,
            "total_posts": 0,
            "high_risk_count": 0,
            "medium_risk_count": 0,
            "low_risk_count": 0,
            "review_count": 0,
            "duplicate_ratio": 0.0,
            "burst_ratio": 0.0,
            "clusters_detected": 0,
            "average_score": 0.0,
        },
        "repeatedPhrases": [],
        "networkNodes": [],
        "networkEdges": [],
        "sentiment": {
            "method": "not-available",
            "disclaimer": "Dataset ini tidak berisi postingan mentah yang diperlukan untuk analisis konteks.",
            "total_posts": 0,
            "counts": {"positive": 0, "negative": 0, "neutral": 0, "mixed": 0},
            "percentages": {"positive": 0.0, "negative": 0.0, "neutral": 0.0, "mixed": 0.0},
            "average_score": 0.0,
            "dominant": "neutral",
            "examples": [],
        },
        "evidence": {
            "topHubs": [],
            "repeatedPhraseCount": 0,
            "sentimentMethod": "not-available",
            "validEdgeEvents": 0,
        },
        "graph": {
            "graph_nodes": 0,
            "graph_edges": 0,
            "total_nodes": 0,
            "total_edges": 0,
            "network_nodes": 0,
            "network_edges": 0,
            "components": 0,
            "largest_component_size": 0,
            "hub": None,
        },
        "warnings": [warning] if warning else [],
    }


def _static_catalog() -> dict[str, Any]:
    frame, source = _catalog_frame()
    if frame.empty:
        result = _empty_analysis_contract(source=source)
        result["total"] = 0
        return result
    profiles = _profile_metadata()
    rows = []
    for row in frame.to_dict("records"):
        dataset_id = str(_catalog_value(row, "dataset_id"))
        account_id = str(_catalog_value(row, "account_id"))
        profile = profiles.get((dataset_id, account_id), {})
        enriched = dict(row)
        for key in ("name", "created", "followers", "following", "statuses", "n_posts", "post_rate", "burst_ratio_1h", "out_degree", "component_size", "bio", "avatar"):
            if _catalog_value(enriched, key) in ("", 0):
                value = _catalog_value(profile, key)
                if value not in ("", 0):
                    enriched[key] = value
        rows.append(enriched)
    accounts = [_catalog_account(row) for row in rows]
    post_counts = pd.to_numeric(
        pd.Series([_catalog_value(row, "n_posts", 0) for row in rows]),
        errors="coerce",
    ).fillna(0)
    result = _empty_analysis_contract(source=source)
    result["accounts"] = accounts
    result["total"] = len(accounts)
    result["summary"].update({
        "total_accounts": len(accounts),
        "total_posts": int(post_counts.sum()),
        "high_risk_count": sum(account["riskLevel"] == "high" for account in accounts),
        "medium_risk_count": sum(account["riskLevel"] == "medium" for account in accounts),
        "low_risk_count": sum(account["riskLevel"] == "low" for account in accounts),
        "review_count": sum(account.get("prediction") == "Review" for account in accounts),
        "average_score": round(sum(account["buzzerScore"] for account in accounts) / len(accounts), 2) if accounts else 0.0,
    })
    result["warnings"] = [
        "Offline catalog berisi skor akun dan metadata profil; jalankan analisis sampel postingan untuk graf, sentimen, dan bukti teks.",
    ]
    return result


@app.get("/api/v1/accounts")
def accounts_catalog() -> dict[str, Any]:
    return _static_catalog()


@app.get("/api/v1/scraper/accounts")
async def scraper_accounts(x_coordinx_admin_token: str | None = Header(default=None)) -> dict[str, Any]:
    require_admin(x_coordinx_admin_token)
    return {"accounts": await accounts_status_async()}


@app.post("/api/v1/scraper/accounts")
async def add_scraper_account(credentials: AccountCredentials, x_coordinx_admin_token: str | None = Header(default=None)) -> dict[str, Any]:
    require_admin(x_coordinx_admin_token)
    if credentials.auth_token and credentials.ct0:
        return {"account": await configure_session_async(f"auth_token={credentials.auth_token}; ct0={credentials.ct0}")}
    try:
        return await account_manager.add_and_login(**credentials.model_dump())
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/health")
@app.get("/api/v1/health")
def health() -> dict[str, Any]:
    model_dir = root / "models" / "final"
    required = ("indobertweet_final.pkl", "temporal_lstm_final.pt", "graphsage_final.pt")
    return {
        "status": "ok" if all((model_dir / name).exists() for name in required) else "degraded",
        "model_artifacts": all((model_dir / name).exists() for name in required),
        "scraper_db": (root / "screpping" / "accounts.db").exists() or (root / "accounts.db").exists(),
        "model_loaded": get_engine.cache_info().currsize > 0,
    }


@app.get("/api/v1/model")
def model_info() -> dict[str, Any]:
    info = model_adapter.metadata()
    info["live_engine"] = {
        "version": "coordinx-final-v1.0.0",
        "components": {"nlp": "IndoBERTweet", "temporal": "TemporalLSTM", "graph": "GraphSAGE"},
    }
    return info


@app.post("/api/v1/analyze")
async def analyze(request: AnalyzeRequest, x_coordinx_admin_token: str | None = Header(default=None)) -> dict[str, Any]:
    try:
        if request.dataset_path:
            dataset_path = _safe_dataset_path(request.dataset_path)
            if dataset_path == root / "output" / "final_model" / "final_predictions.csv":
                return _static_catalog()
            frame = await run_in_threadpool(pd.read_csv, dataset_path, dtype="string", keep_default_na=True)
            if {"post_id", "account_id", "text", "date"}.issubset(frame.columns):
                result = await run_in_threadpool(get_engine().predict, frame, str(dataset_path))
                result["source"] = "dataset"
                return result
            result = await run_in_threadpool(model_adapter.predict, frame)
            metadata = model_adapter.metadata()
            response = _empty_analysis_contract(
                source="model",
                query=str(dataset_path),
                model_version=metadata.get("version", ""),
                warning=metadata.get("warning"),
            )
            response["model"] = metadata
            response["summary"]["total_accounts"] = len(result.probability_buzzer)
            response["warnings"].append(
                "Dataset hanya berisi fitur agregat; gunakan CSV postingan mentah untuk mengisi graf, sentimen, dan bukti teks."
            )
            return response

        if not request.query:
            raise HTTPException(status_code=400, detail="dataset_path atau query wajib diisi")
        require_admin(x_coordinx_admin_token)
        statuses = await accounts_status_async()
        if not any(account.get("active") for account in statuses):
            fallback = await _local_dataset_fallback(
                request.query,
                request.limit,
                "Tidak ada akun twscrape aktif.",
            )
            if fallback is not None:
                return fallback
            raise HTTPException(status_code=422, detail="Belum ada akun twscrape aktif. Tambahkan akun melalui admin setup.")
        try:
            raw = await asyncio.wait_for(
                scrape_async(
                    query=request.query,
                    limit=request.limit,
                    cookies="",
                    fetch_replies=request.fetch_replies or "/status/" in request.query,
                    days=None if "/status/" in request.query else request.days,
                ),
                timeout=float(os.getenv("COORDINX_SCRAPE_TIMEOUT_SECONDS", "105")),
            )
        except Exception as exc:
            fallback = await _local_dataset_fallback(request.query, request.limit, str(exc))
            if fallback is not None:
                return fallback
            raise HTTPException(status_code=422, detail=f"Scraping live X gagal: {exc}") from exc
        return await run_in_threadpool(get_engine().predict, raw, request.query)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Analisis tidak dapat dijalankan: {exc}") from exc
