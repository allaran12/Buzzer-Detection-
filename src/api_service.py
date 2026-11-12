"""FastAPI service for CoordinX live scraping and final-model inference.

Run from the repository root with:
    uvicorn src.api_service:app --host 127.0.0.1 --port 8000
"""
from __future__ import annotations

import asyncio
import json
import os
import re
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import pandas as pd
from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

try:
    import uvloop
except ImportError:
    pass
else:
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from inference.live_model_inference import LiveModelEngine  # noqa: E402
from screpping import accounts_status_async, configure_session_async, scrape_async  # noqa: E402


MODEL_DIR = ROOT / "models" / "final"
FINAL_PREDICTIONS = ROOT / "output" / "final_model" / "final_predictions.csv"
ALLOWED_DATA_ROOTS = (ROOT / "data", ROOT / "output")

app = FastAPI(title="CoordinX Inference API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in os.getenv("COORDINX_CORS_ORIGINS", "http://localhost:3000").split(",") if origin.strip()],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "x-coordinx-admin-token"],
)


class AnalyzeRequest(BaseModel):
    query: str | None = None
    dataset_path: str | None = None
    limit: int = Field(default=25, ge=1, le=500)
    fetch_replies: bool = False
    days: int | None = Field(default=30, ge=1, le=365)
    model_experiment: str | None = None


class ScraperSessionRequest(BaseModel):
    auth_token: str = Field(min_length=1)
    ct0: str = Field(min_length=1)


def _admin_guard(token: str | None = Header(default=None, alias="x-coordinx-admin-token")) -> None:
    expected = os.getenv("COORDINX_ADMIN_TOKEN")
    if not expected:
        if os.getenv("COORDINX_ENV", "local").lower() == "production":
            raise HTTPException(status_code=503, detail="COORDINX_ADMIN_TOKEN belum dikonfigurasi")
        expected = "local-admin"
    if token != expected:
        raise HTTPException(status_code=401, detail="Admin token tidak valid")


def _engine() -> LiveModelEngine:
    return LiveModelEngine(ROOT)


@lru_cache(maxsize=1)
def get_engine() -> LiveModelEngine:
    return _engine()


def _validate_query(value: str) -> str:
    query = value.strip()
    if not query:
        raise HTTPException(status_code=400, detail="URL atau query analisis wajib diisi")
    parsed = urlparse(query)
    if parsed.scheme and parsed.netloc:
        if parsed.scheme.lower() not in {"http", "https"}:
            raise HTTPException(status_code=400, detail="URL harus menggunakan http atau https")
        host = parsed.netloc.lower().split(":", 1)[0].removeprefix("www.")
        if host not in {"x.com", "twitter.com", "mobile.twitter.com", "mobile.x.com"}:
            raise HTTPException(status_code=400, detail="URL harus berasal dari x.com atau twitter.com")
        is_post = re.search(r"/status/\d+(?:/)?$", parsed.path) is not None
        is_hashtag = parsed.path.startswith("/hashtag/")
        is_search = parsed.path.startswith("/search")
        if not (is_post or is_hashtag or is_search):
            raise HTTPException(status_code=400, detail="URL X harus berupa postingan, hashtag, atau pencarian")
    return query


def _safe_dataset_path(value: str) -> Path:
    candidate = Path(value)
    if not candidate.is_absolute():
        candidate = ROOT / candidate
    resolved = candidate.resolve()
    if not any(resolved == allowed or allowed in resolved.parents for allowed in ALLOWED_DATA_ROOTS):
        raise HTTPException(status_code=400, detail="dataset_path berada di luar direktori data/output yang diizinkan")
    if not resolved.exists() or not resolved.is_file():
        raise HTTPException(status_code=404, detail=f"Dataset tidak ditemukan: {value}")
    return resolved


def _catalog_account(row: dict[str, Any]) -> dict[str, Any]:
    probability = float(row.get("probability_buzzer") or 0)
    prediction = str(row.get("prediction") or "Review")
    risk = str(row.get("risk_level") or ("high" if probability >= 0.65 else "low" if probability <= 0.35 else "medium"))
    username = str(row.get("username") or "unknown")
    return {
        "id": str(row.get("account_id") or row.get("account_key") or username),
        "username": username,
        "name": username,
        "avatar": "",
        "bio": "",
        "created": "",
        "accountAgeDays": 0,
        "followers": 0,
        "following": 0,
        "followerRatio": 0,
        "statuses": 0,
        "statusesPerDay": 0,
        "buzzerScore": round(probability * 100, 2),
        "riskLevel": risk,
        "campaignIssue": str(row.get("issue_id") or row.get("dataset_id") or ""),
        "nPostsInDataset": int(float(row.get("n_posts") or 0)),
        "postRatePerHour": float(row.get("post_rate") or 0),
        "duplicateTextRatio": float(row.get("max_peer_similarity") or 0),
        "burstRatio": float(row.get("burst_ratio_1h") or 0),
        "outDegree": int(float(row.get("out_degree") or 0)),
        "clusterId": None,
        "indicators": [],
        "tweets": [],
        "probabilityBuzzer": probability,
        "confidence": float(row.get("confidence") or abs(probability - 0.5) * 2),
        "prediction": prediction,
        "reviewStatus": str(row.get("review_status") or "MODEL_OUTPUT"),
        "explanation": str(row.get("explanation") or ""),
        "branchScores": _parse_branch_scores(row.get("branch_scores")),
    }


def _parse_branch_scores(value: Any) -> dict[str, float]:
    if not value or pd.isna(value):
        return {}
    try:
        decoded = json.loads(str(value))
        return {str(key): float(item) for key, item in decoded.items()}
    except (TypeError, ValueError, json.JSONDecodeError):
        return {}


def _static_catalog() -> dict[str, Any]:
    if not FINAL_PREDICTIONS.exists():
        raise HTTPException(status_code=503, detail="Final predictions belum tersedia")
    frame = pd.read_csv(FINAL_PREDICTIONS, dtype="string", keep_default_na=True)
    accounts = [_catalog_account(row) for row in frame.to_dict("records")]
    scores = [account["buzzerScore"] for account in accounts]
    return {
        "source": "final_contract",
        "query": None,
        "modelVersion": "coordinx-final-v1.0.0",
        "accounts": accounts,
        "summary": {
            "total_accounts": len(accounts),
            "total_posts": int(pd.to_numeric(frame.get("n_posts"), errors="coerce").fillna(0).sum()) if "n_posts" in frame else 0,
            "high_risk_count": sum(account["riskLevel"] == "high" for account in accounts),
            "medium_risk_count": sum(account["riskLevel"] == "medium" for account in accounts),
            "low_risk_count": sum(account["riskLevel"] == "low" for account in accounts),
            "review_count": sum(account["prediction"] == "Review" for account in accounts),
            "average_score": round(sum(scores) / len(scores), 2) if scores else 0,
            "duplicate_ratio": round(float(pd.to_numeric(frame.get("max_peer_similarity"), errors="coerce").fillna(0).mean()), 4) if "max_peer_similarity" in frame else 0,
            "burst_ratio": round(float(pd.to_numeric(frame.get("burst_ratio_1h"), errors="coerce").fillna(0).mean()), 4) if "burst_ratio_1h" in frame else 0,
        },
    }


@app.get("/health")
@app.get("/api/v1/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "model_artifacts": all((MODEL_DIR / name).exists() for name in ("indobertweet_final.pkl", "temporal_lstm_final.pt", "graphsage_final.pt")),
        "scraper_db": (ROOT / "screpping" / "accounts.db").exists(),
        "model_loaded": get_engine.cache_info().currsize > 0,
    }


@app.post("/api/v1/analyze")
async def analyze(request: AnalyzeRequest) -> dict[str, Any]:
    if request.dataset_path:
        dataset_path = _safe_dataset_path(request.dataset_path)
        if dataset_path == FINAL_PREDICTIONS:
            return _static_catalog()
        try:
            frame = await run_in_threadpool(pd.read_csv, dataset_path, dtype="string", keep_default_na=True)
            result = await run_in_threadpool(get_engine().predict, frame, str(dataset_path))
            result["source"] = "dataset"
            return result
        except HTTPException:
            raise
        except Exception as error:
            raise HTTPException(status_code=422, detail=f"Dataset tidak dapat diproses: {error}") from error

    query = _validate_query(request.query or "")
    try:
        raw = await asyncio.wait_for(
            scrape_async(
                query=query,
                limit=request.limit,
                cookies=os.getenv("COORDINX_SCRAPER_COOKIES", ""),
                fetch_replies=request.fetch_replies or "/status/" in query,
                days=None if "/status/" in query else request.days,
            ),
            timeout=float(os.getenv("COORDINX_SCRAPE_TIMEOUT_SECONDS", "105")),
        )
        result = await run_in_threadpool(get_engine().predict, raw, query)
        return result
    except HTTPException:
        raise
    except Exception as error:
        message = str(error).strip() or error.__class__.__name__
        raise HTTPException(status_code=502, detail=f"Scrape/inference gagal: {message}") from error


@app.get("/api/v1/accounts")
def accounts(
    risk: str | None = Query(default=None),
    issue: str | None = Query(default=None),
    q: str | None = Query(default=None),
) -> dict[str, Any]:
    result = _static_catalog()
    values = result["accounts"]
    if risk and risk != "all":
        values = [account for account in values if account["riskLevel"] == risk]
    if issue and issue != "all":
        values = [account for account in values if account["campaignIssue"] == issue]
    if q:
        needle = q.casefold()
        values = [account for account in values if needle in f"{account['username']} {account['name']} {account['bio']}".casefold()]
    result["accounts"] = values
    result["total"] = len(values)
    return result


@app.get("/api/v1/scraper/accounts", dependencies=[Depends(_admin_guard)])
async def scraper_accounts() -> dict[str, Any]:
    try:
        return {"accounts": await accounts_status_async()}
    except Exception as error:
        raise HTTPException(status_code=502, detail=f"Gagal membaca akun scraper: {error}") from error


@app.post("/api/v1/scraper/accounts", dependencies=[Depends(_admin_guard)])
async def scraper_session(request: ScraperSessionRequest) -> dict[str, Any]:
    cookies = f"auth_token={request.auth_token}; ct0={request.ct0}"
    try:
        account = await configure_session_async(cookies)
        return {"account": account}
    except Exception as error:
        raise HTTPException(status_code=422, detail=f"Session scraper tidak valid: {error}") from error
