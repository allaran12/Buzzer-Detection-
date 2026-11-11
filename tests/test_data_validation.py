#!/usr/bin/env python3
"""
Unit tests for CoordinX Data Validation & Ingestion (PRD Phase 1).
No external frameworks; runs with stdlib assert.
"""
import sys
import io
import hashlib
from pathlib import Path
import pandas as pd

sys.path.insert(0, "src/preprocessing")
from cleaning import clean_dataset, apply_column_mapping
from standardization import standardize_dataset

def test_column_mapping():
    # Test alias mapping (id -> post_id, tweet -> text, etc.)
    df = pd.DataFrame([{
        "id": "1234567890123456789",
        "user_id": "9876543210987654321",
        "tweet": "Hello world",
        "created_at": "2026-11-09 10:00:00",
        "screen_name": "user_a",
    }])
    mapped = apply_column_mapping(df)
    assert "post_id" in mapped.columns, "Failed to map 'id' to 'post_id'"
    assert "account_id" in mapped.columns, "Failed to map 'user_id' to 'account_id'"
    assert "text" in mapped.columns, "Failed to map 'tweet' to 'text'"
    assert "date" in mapped.columns, "Failed to map 'created_at' to 'date'"
    assert "username" in mapped.columns, "Failed to map 'screen_name' to 'username'"

def test_id_preservation():
    # Test very long snowflake IDs are preserved as string, not truncated float
    long_id = "2119321404298645606"
    df = pd.DataFrame([{
        "post_id": long_id,
        "account_id": "1810223652115484672",
        "date": "2026-11-08 06:49:32+00:00",
        "text": "Sample tweet text",
        "username": "tester",
        "relation_type": "original",
        "is_rt": "False", "is_reply": "False", "is_quote": "False"
    }])
    cleaned, _, _, _ = clean_dataset(df)
    assert cleaned["post_id"].iloc[0] == long_id, "ID was corrupted in cleaning"

    standardized, _ = standardize_dataset(cleaned)
    assert standardized["post_id"].iloc[0] == long_id, "ID was corrupted in standardization"
    assert standardized["post_id"].dtype == "string", "ID is not string type"

def test_deduplication():
    # Duplicate post_id must be removed, but duplicate text with different post_id must be kept
    df = pd.DataFrame([
        {"post_id": "1", "account_id": "A", "date": "2026-11-01", "text": "Same text", "username": "u1", "relation_type": "original", "is_rt": "False", "is_reply": "False", "is_quote": "False"},
        {"post_id": "1", "account_id": "A", "date": "2026-11-01", "text": "Same text", "username": "u1", "relation_type": "original", "is_rt": "False", "is_reply": "False", "is_quote": "False"},
        {"post_id": "2", "account_id": "B", "date": "2026-11-01", "text": "Same text", "username": "u2", "relation_type": "original", "is_rt": "False", "is_reply": "False", "is_quote": "False"},
    ])
    cleaned, dupes, _, report = clean_dataset(df)
    assert len(cleaned) == 2, f"Expected 2 rows after dedup, got {len(cleaned)}"
    assert len(dupes) == 1, "Duplicate post_id was not caught"
    assert set(cleaned["post_id"]) == {"1", "2"}, "Wrong post_ids kept"

def test_empty_text_and_missing_identity():
    # Empty text or missing post_id/account_id must be rejected
    df = pd.DataFrame([
        {"post_id": "", "account_id": "A", "date": "2026-11-01", "text": "Valid", "username": "u1", "relation_type": "original", "is_rt": "False", "is_reply": "False", "is_quote": "False"},
        {"post_id": "2", "account_id": "", "date": "2026-11-01", "text": "Valid", "username": "u2", "relation_type": "original", "is_rt": "False", "is_reply": "False", "is_quote": "False"},
        {"post_id": "3", "account_id": "C", "date": "2026-11-01", "text": "   ", "username": "u3", "relation_type": "original", "is_rt": "False", "is_reply": "False", "is_quote": "False"},
        {"post_id": "4", "account_id": "D", "date": "2026-11-01", "text": "Valid tweet", "username": "u4", "relation_type": "original", "is_rt": "False", "is_reply": "False", "is_quote": "False"},
    ])
    cleaned, _, rejected, _ = clean_dataset(df)
    assert len(cleaned) == 1, f"Expected 1 valid row, got {len(cleaned)}"
    assert len(rejected) == 3, f"Expected 3 rejected rows, got {len(rejected)}"
    assert cleaned["post_id"].iloc[0] == "4"

def test_raw_file_unmodified():
    # PRD FR: Raw data must remain untouched
    raw_path = Path("data/raw/RoySuryo.csv")
    if raw_path.exists():
        h1 = hashlib.sha256(raw_path.read_bytes()).hexdigest()
        from ingest import run_ingest
        run_ingest(str(raw_path))
        h2 = hashlib.sha256(raw_path.read_bytes()).hexdigest()
        assert h1 == h2, "Raw dataset was modified by ingest pipeline!"

if __name__ == "__main__":
    test_column_mapping()
    test_id_preservation()
    test_deduplication()
    test_empty_text_and_missing_identity()
    test_raw_file_unmodified()
    print("✓ All Phase 1 Data Validation tests PASSED!")
