#!/usr/bin/env python3
"""Assert-based checks for canonical regeneration, retraining, and Phase 7."""
from pathlib import Path
import json
import pickle
import sys

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from features.canonical_features import CANONICAL_ACCOUNT_COLUMNS  # noqa: E402


def _read(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype="string", keep_default_na=True)


def test_canonical_data():
    expected = {
        "batch2": {"posts": 1514, "accounts": 1007, "labels": {"0": 27, "1": 23}},
        "batch3": {"posts": 1081, "accounts": 796, "labels": {"0": 21, "1": 29}},
    }
    for batch, values in expected.items():
        validation = json.loads((ROOT / "data" / "features" / f"{batch}_validation.json").read_text())
        assert validation["post"]["posts"] == values["posts"]
        assert validation["account_features"]["rows"] == values["accounts"]
        assert validation["label_preservation"]["canonical_counts"] == values["labels"]
        posts = _read(ROOT / "data" / "features" / f"{batch}_posts_with_features.csv")
        accounts = _read(ROOT / "data" / "features" / f"{batch}_account_features.csv")
        interactions = _read(ROOT / "data" / "features" / f"{batch}_interactions.csv")
        labels = _read(ROOT / "data" / "labels" / f"{batch}_labeled_canonical.csv")
        assert len(posts) == values["posts"]
        assert len(accounts) == values["accounts"]
        assert accounts.columns.tolist() == CANONICAL_ACCOUNT_COLUMNS
        assert accounts["account_id"].notna().all()
        assert accounts["account_id"].is_unique
        assert posts["post_id"].notna().all()
        assert posts["post_id"].is_unique
        valid_edges = interactions[interactions["is_valid_edge"] == "True"]
        assert valid_edges["source_account_id"].notna().all()
        assert valid_edges["target_account_id"].notna().all()
        assert (valid_edges["source_account_id"] != valid_edges["target_account_id"]).all()
        assert len(labels) == 50
        for column in ["account_id", "post_id", "target_account_id"]:
            if column not in posts:
                continue
            values_to_check = posts[column].dropna().astype(str)
            assert not values_to_check.str.contains(r"[eE][+-]?\d+", regex=True).any()


def test_manual_labels_are_preserved():
    for batch in ("batch2", "batch3"):
        original = _read(ROOT / "data" / "labels" / f"{batch}_labeled_combined.csv")
        canonical = _read(ROOT / "data" / "labels" / f"{batch}_labeled_canonical.csv")
        original_map = dict(zip(original["username"], pd.to_numeric(original["label"], errors="coerce").astype(int)))
        canonical_map = dict(zip(canonical["username"], pd.to_numeric(canonical["label"], errors="coerce").astype(int)))
        assert original_map == canonical_map


def test_retrained_models_and_phase7():
    for experiment in ("batch2", "batch3", "combined"):
        model_path = ROOT / "models" / f"phase6_fusion_proxy_{experiment}_canonical.pkl"
        metrics_path = ROOT / "output" / "phase6_canonical" / experiment / "phase6_group_cv_metrics.csv"
        assert model_path.exists()
        assert metrics_path.exists()
        with model_path.open("rb") as handle:
            artifact = pickle.load(handle)
        assert artifact["schema_version"] == "canonical-v1"
        assert "buzzer_score" not in artifact["feature_columns"]
        assert artifact["advanced_backends"] == {
            "indobertweet": False,
            "lstm": False,
            "graphsage": False,
        }
        metrics = _read(metrics_path)
        assert set(metrics["model"]) == {"text_proxy", "temporal_proxy", "graph_proxy", "fusion_proxy"}

    predictions = _read(ROOT / "output" / "phase7" / "phase7_predictions.csv")
    assert len(predictions) == 1803
    assert not predictions.duplicated(subset=["dataset_id", "account_id"]).any()
    assert predictions["coordination_score"].notna().all()
    assert predictions["uncertainty"].notna().all()
    assert set(predictions["review_status"]) <= {"REVIEW_REQUIRED", "PRIORITY_REVIEW", "LOW_PRIORITY"}


if __name__ == "__main__":
    test_canonical_data()
    test_manual_labels_are_preserved()
    test_retrained_models_and_phase7()
    print("Canonical pipeline checks PASSED")
