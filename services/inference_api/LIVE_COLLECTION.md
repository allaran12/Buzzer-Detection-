# Live X collection

The inference API now supports `query` values that are X status URLs, hashtag URLs, search URLs, or search strings. It uses the canonical `src/screpping.py` collector and then builds canonical account features before running the final model.

Configure twscrape accounts in `accounts.db` before using live collection. The collector requires at least one active account. Do not commit credentials or cookies. When live collection is unavailable, known research topics transparently use a matching local CSV and return `source: local_dataset_fallback`; unrelated topics still return an actionable error.

Run the service with the final environment:

```bash
source .venv-final/bin/activate
PYTHONPATH=. uvicorn services.inference_api.main:app --reload
```

Example request:

```bash
curl -X POST http://localhost:8000/api/v1/analyze \
  -H 'Content-Type: application/json' \
  -d '{"query":"https://x.com/user/status/123","limit":200,"fetch_replies":true,"days":30}'
```

If no active scraper account is configured, the API uses the matching local sample when available; otherwise it returns a clear `422` error instead of fabricated analysis results.
