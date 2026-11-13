# Backend Consolidation and Audit Finalization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make `services.inference_api.main` the canonical backend, align frontend contracts, fix reproduced P0/P1 issues, add meaningful verification, and document the audited result without deleting user data.

**Architecture:** Keep the existing FastAPI, Next.js, twscrape, SQLite, and model pipeline. Use the newer inference service as the runtime backend and preserve the legacy service only as non-canonical code until migration is verified. Centralize security and response behavior at the canonical API boundary.

**Tech Stack:** Python 3.15, FastAPI, Pydantic, twscrape, SQLite, pandas/scikit-learn, Next.js 16, TypeScript, ESLint.

**Spec:** Approved backend consolidation design from the user conversation.

## Global Constraints

- Do not reset, delete, or overwrite user data, databases, credentials, or uncommitted user changes.
- Do not expose secrets in logs, responses, or audit documentation.
- Do not rewrite the system or replace its framework.
- Use tests before production changes for behavioral fixes.
- Report unavailable external-service and dependency checks as limitations.

## Review Focus

- Missing or invalid admin credentials must be rejected without a predictable production fallback; test canonical auth behavior.
- Partial scraper credentials must fail clearly and complete cookie credentials must remain usable; test account validation.
- Frontend-used API routes must exist on the canonical backend; test route compatibility.
- Dataset paths and analysis requests must not expose arbitrary files or caller-supplied secrets; test path and request validation.
- Model probability output must honor class labels rather than column position; test reversed class ordering.

### Task 1: Canonical backend contract and security

**Files:** Modify `services/inference_api/main.py`, `web/src/app/api/accounts/route.ts`, `web/src/app/api/analyze/route.ts`, add focused tests under `tests/`.

- Add/align `/api/v1/accounts` compatibility behavior or update the proxy to a canonical existing contract.
- Make admin auth explicit for production while preserving local-only development behavior.
- Remove caller cookie forwarding from public analysis requests and validate dataset paths.
- Normalize API error responses and remove dead exception handling.
- Add failing tests for auth, route contract, and cookie/path restrictions, then run pytest.

### Task 2: Scraper account and inference correctness

**Files:** Modify `services/inference_api/account_manager.py`, `src/inference/live_pipeline.py`, `src/inference/model_adapter.py`; add tests.

- Support either complete cookie credentials or complete password credentials with clear rejection of partial input.
- Normalize account status without exposing cookie values.
- Align effective scrape limit/defaults and return explicit effective behavior.
- Resolve model class-label probability selection and verify feature schema.
- Add failing tests, implement minimally, and run focused plus full Python checks.

### Task 3: Frontend resilience and validation

**Files:** Modify `web/src/app/admin/scraper/page.tsx`, relevant proxy routes, and only necessary UI files.

- Handle network/non-JSON backend failures safely.
- Keep admin form state and messages consistent without leaking secrets.
- Remove unused lint issues where behavior is unchanged.
- Run lint, typecheck, and production build.

### Task 4: Audit tests, documentation, and final verification

**Files:** Create `FINAL_AUDIT_REPORT.md`; add/update tests and `.gitignore` only where safe.

- Make test execution reproducible from repository root.
- Run compile, pytest if available, pip check, frontend lint/typecheck/build, route smoke tests, and security checks.
- Record actual results, unresolved external limitations, file counts, fixes, and final status.
- Never claim READY if critical tests remain blocked.
