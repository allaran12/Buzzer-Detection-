#!/usr/bin/env python3
"""Small assert-based checks for Phase 6 artifacts."""
from pathlib import Path
import sys
import pickle
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from models.phase6_advanced import TextColumnExtractor  # noqa: F401


def test_phase6_artifacts():
    model_path = ROOT / "models" / "phase6_fusion_proxy.pkl"
    metrics_path = ROOT / "output" / "phase6" / "phase6_group_cv_metrics.csv"
    report_path = ROOT / "reports" / "PHASE6_ADVANCED_MODELING_REPORT.md"

    assert model_path.exists(), "Missing Phase 6 model artifact"
    assert metrics_path.exists(), "Missing Phase 6 metrics"
    assert report_path.exists(), "Missing Phase 6 report"

    with model_path.open("rb") as handle:
        artifact = pickle.load(handle)

    assert artifact["training_batches"] == ["batch2", "batch3"]
    assert artifact["training_rows"] == 100
    assert "buzzer_score" not in artifact["feature_columns"]
    assert "label" not in artifact["feature_columns"]
    assert artifact["advanced_backends"] == {
        "indobertweet": False,
        "lstm": False,
        "graphsage": False,
    }

    metrics = pd.read_csv(metrics_path)
    assert set(metrics["model"]) == {
        "text_proxy", "temporal_proxy", "graph_proxy", "fusion_proxy"
    }
    assert len(metrics) == 4


if __name__ == "__main__":
    test_phase6_artifacts()
    print("✓ Phase 6 artifact checks PASSED!")
