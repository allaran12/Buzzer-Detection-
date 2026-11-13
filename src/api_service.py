"""Compatibility entrypoint for the canonical CoordinX inference API.

The implementation lives in ``services.inference_api.main``. Keeping this
module as a thin re-export prevents older launch commands from using a stale
response contract.
"""
from services.inference_api.main import (
    AccountCredentials,
    AnalyzeRequest,
    accounts_catalog,
    add_scraper_account,
    analyze,
    app,
    health,
    model_info,
    require_admin,
    scraper_accounts,
)

__all__ = [
    "AccountCredentials",
    "AnalyzeRequest",
    "accounts_catalog",
    "add_scraper_account",
    "analyze",
    "app",
    "health",
    "model_info",
    "require_admin",
    "scraper_accounts",
]
