#!/usr/bin/env python3
"""Read and validate the research-final prediction contract.

This module is intentionally independent from the `/web` adapter. It gives the
future API a stable artifact contract without starting web integration early.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


REQUIRED_COLUMNS = {
    "account_id", "username", "dataset_id", "issue_id", "prediction",
    "coordination_score", "probability_buzzer", "confidence", "risk_level",
    "indobertweet_probability", "temporal_lstm_probability", "graphsage_probability",
    "explanation", "review_status", "model_version", "schema_version",
}


def find_repo_root(root: str | Path | None = None) -> Path:
    if root is not None:
        path = Path(root).resolve()
    else:
        path = Path.cwd().resolve()
        while path != path.parent and not (path / "PRD.md").exists():
            path = path.parent
    if not (path / "PRD.md").exists():
        raise FileNotFoundError("Repository root dengan PRD.md tidak ditemukan")
    return path


def load_final_contract(root: str | Path | None = None) -> dict[str, Any]:
    root_path = find_repo_root(root)
    readiness_path = root_path / "output" / "final_model" / "final_readiness.json"
    if not readiness_path.exists():
        raise FileNotFoundError(f"Final readiness tidak ditemukan: {readiness_path}")
    return json.loads(readiness_path.read_text(encoding="utf-8"))


def load_final_predictions(root: str | Path | None = None, review_only: bool = False) -> pd.DataFrame:
    root_path = find_repo_root(root)
    path = root_path / "output" / "final_model" / "final_predictions.csv"
    if not path.exists():
        raise FileNotFoundError(f"Final predictions tidak ditemukan: {path}")
    frame = pd.read_csv(path, dtype="string", keep_default_na=True)
    missing = REQUIRED_COLUMNS - set(frame.columns)
    if missing:
        raise ValueError(f"Kolom output final hilang: {sorted(missing)}")
    if frame[["dataset_id", "account_id"]].duplicated().any():
        raise ValueError("Final predictions duplicate pada dataset_id/account_id")
    if not set(frame["prediction"].dropna()).issubset({"Buzzer", "Organic", "Review"}):
        raise ValueError("Prediction final di luar kontrak Buzzer/Organic/Review")
    if review_only:
        frame = frame[frame["review_status"] == "REVIEW_REQUIRED"].copy()
    return frame


def get_account_prediction(
    account_id: str,
    dataset_id: str | None = None,
    root: str | Path | None = None,
) -> dict[str, Any] | None:
    frame = load_final_predictions(root)
    mask = frame["account_id"].astype(str).eq(str(account_id))
    if dataset_id is not None:
        mask &= frame["dataset_id"].astype(str).eq(str(dataset_id))
    rows = frame.loc[mask]
    if rows.empty:
        return None
    return rows.iloc[0].to_dict()


if __name__ == "__main__":
    contract = load_final_contract()
    predictions = load_final_predictions()
    print(json.dumps({
        "status": contract["status"],
        "rows": len(predictions),
        "model_version": contract["model_version"],
    }, indent=2, ensure_ascii=False))
