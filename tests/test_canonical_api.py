import os
import unittest
from unittest.mock import AsyncMock, patch

from fastapi import HTTPException

from services.inference_api.main import AnalyzeRequest, _local_dataset_for_query, _static_catalog, analyze, app, require_admin


class CanonicalApiContractTests(unittest.IsolatedAsyncioTestCase):
    def test_production_requires_explicit_admin_token(self):
        with patch.dict(os.environ, {"COORDINX_ENV": "production"}, clear=True):
            with self.assertRaises(HTTPException):
                require_admin("local-admin")

    def test_analysis_request_rejects_caller_cookies(self):
        with self.assertRaises(ValueError):
            AnalyzeRequest.model_validate({"query": "#test", "cookies": "auth_token=secret"})

    def test_canonical_backend_exposes_accounts_route(self):
        routes = {route.path for route in app.routes}
        self.assertIn("/api/v1/accounts", routes)

    def test_legacy_entrypoint_reexports_canonical_app(self):
        from src.api_service import app as legacy_app

        self.assertIs(legacy_app, app)

    def test_accounts_catalog_has_profile_media_when_offline_predictions_exist(self):
        catalog = _static_catalog()
        self.assertGreater(catalog["total"], 0)
        self.assertTrue(any(account.get("avatar", "").startswith("https://pbs.twimg.com/") for account in catalog["accounts"]))
        self.assertIn("networkNodes", catalog)
        self.assertIn("networkEdges", catalog)
        self.assertIn("sentiment", catalog)
        self.assertIn("repeatedPhrases", catalog)
        self.assertIn("evidence", catalog)

    def test_known_query_resolves_to_local_dataset(self):
        self.assertTrue(_local_dataset_for_query("#RoySuryo").name == "RoySuryo.csv")
        self.assertTrue(_local_dataset_for_query("https://x.com/hashtag/prayforkalimantan").name == "prayforkalimantan.csv")
        self.assertTrue(_local_dataset_for_query("https://x.com/user/status/2119413607498748059").name == "RoySuryo.csv")
        self.assertTrue(_local_dataset_for_query("https://x.com/cariaeosa/status/2120526926364410130").name == "wowo2.csv")
        self.assertIsNone(_local_dataset_for_query("#topic-not-in-catalog"))

    async def test_live_scrape_failure_returns_complete_local_contract(self):
        fake_result = {
            "source": "live_scrape",
            "query": "#RoySuryo",
            "summary": {"total_posts": 3},
            "accounts": [],
            "networkNodes": [{"id": "1"}],
            "networkEdges": [{"source": "1", "target": "2"}],
            "sentiment": {"method": "fixture"},
            "repeatedPhrases": [{"phrase": "sample", "count": 2}],
            "evidence": {"validEdgeEvents": 1},
            "warnings": [],
        }
        with patch("services.inference_api.main.accounts_status_async", new=AsyncMock(return_value=[{"active": True}])), \
             patch("services.inference_api.main.scrape_async", new=AsyncMock(side_effect=RuntimeError("No account available for queue SearchTimeline"))), \
             patch("services.inference_api.main.get_engine", return_value=type("Engine", (), {"predict": lambda self, frame, query: fake_result})()):
            response = await analyze(AnalyzeRequest(query="#RoySuryo", limit=3), "local-admin")

        self.assertEqual(response["source"], "local_dataset_fallback")
        self.assertEqual(response["fallback"]["dataset"], "data/raw/RoySuryo.csv")
        self.assertEqual(len(response["networkNodes"]), 1)
        self.assertIn("Scraping live X tidak tersedia", response["warnings"][-2])


if __name__ == "__main__":
    unittest.main()
