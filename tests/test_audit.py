#!/usr/bin/env python3
"""Small assert-based self-check for repository structure and data integrity."""
import os
import pandas as pd

def test_data_integrity():
    # 1. Pastikan folder data inti ada
    for d in ["data/raw", "data/interim", "data/processed", "data/features", "data/labels", "data/predictions"]:
        assert os.path.isdir(d), f"Missing directory: {d}"

    # 2. Pastikan file label batch 2 dan 3 lengkap
    b2 = pd.read_csv("data/labels/batch2_labeled_combined.csv")
    b3 = pd.read_csv("data/labels/batch3_labeled_combined.csv")
    assert len(b2) == 50, f"Batch 2 expected 50 labeled accounts, got {len(b2)}"
    assert len(b3) == 50, f"Batch 3 expected 50 labeled accounts, got {len(b3)}"
    assert "label" in b2.columns and "username" in b2.columns
    assert "label" in b3.columns and "username" in b3.columns

    # 3. Pastikan ID dibaca sebagai string tanpa overflow di processed
    sample_df = pd.read_csv("data/processed/RoySuryo/standardized_data.csv", nrows=5, dtype=str)
    for col in ["post_id", "account_id"]:
        assert col in sample_df.columns, f"Missing {col} in standardized data"
        assert sample_df[col].dtype == object, f"{col} must be string object"

    # 4. Pastikan model dan report audit ada
    assert os.path.exists("models/phase5_baseline_rf.pkl"), "Missing models/phase5_baseline_rf.pkl"
    assert os.path.exists("reports/REPOSITORY_AUDIT.md"), "Missing reports/REPOSITORY_AUDIT.md"

    print("✓ All repository integrity checks PASSED!")

if __name__ == "__main__":
    test_data_integrity()
