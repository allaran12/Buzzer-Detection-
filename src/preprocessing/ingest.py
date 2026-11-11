#!/usr/bin/env python3
"""
Full Ingestion Pipeline (PRD Phase 1)
Chains: Data Cleaning -> Deduplication & Audit -> Standardization
Usage:
    python src/preprocessing/ingest.py --input data/raw/RoySuryo.csv
"""
import argparse
from pathlib import Path
import pandas as pd
from cleaning import clean_dataset, read_csv_safely
from standardization import standardize_dataset

def run_ingest(raw_csv_path: str, interim_dir: str = "data/interim", processed_dir: str = "data/processed"):
    input_path = Path(raw_csv_path)
    file_stem = input_path.stem

    if not input_path.exists():
        raise FileNotFoundError(f"Raw CSV not found: {input_path}")

    # 1. Clean & Audit
    raw_df = read_csv_safely(input_path)
    cleaned, duplicates, rejected, clean_report = clean_dataset(raw_df, default_isu=file_stem)

    interim_out = Path(interim_dir) / file_stem
    interim_out.mkdir(parents=True, exist_ok=True)
    cleaned.to_csv(interim_out / f"{file_stem}_cleaned.csv", index=False, encoding="utf-8-sig")
    duplicates.to_csv(interim_out / f"{file_stem}_duplicates.csv", index=False, encoding="utf-8-sig")
    rejected.to_csv(interim_out / f"{file_stem}_rejected.csv", index=False, encoding="utf-8-sig")

    clean_lines = ["COORDINX - CLEANING REPORT", "=" * 30]
    for k, v in clean_report.items():
        clean_lines.append(f"{k}: {v}")
    (interim_out / f"{file_stem}_report.txt").write_text("\n".join(clean_lines), encoding="utf-8")

    # 2. Standardize
    standardized, std_report = standardize_dataset(cleaned)
    proc_out = Path(processed_dir) / file_stem
    proc_out.mkdir(parents=True, exist_ok=True)
    standardized.to_csv(
        proc_out / "standardized_data.csv",
        index=False,
        encoding="utf-8-sig",
        date_format="%Y-%m-%dT%H:%M:%SZ",
    )

    std_lines = ["COORDINX - STANDARDIZATION REPORT", "=" * 35]
    for k, v in std_report.items():
        std_lines.append(f"{k}: {v}")
    (proc_out / "standardization_report.txt").write_text("\n".join(std_lines), encoding="utf-8")

    print(f"✓ Ingestion complete for '{file_stem}':")
    print(f"  Raw rows:          {clean_report['rows_before']}")
    print(f"  Cleaned rows:      {clean_report['rows_after_cleaning']}")
    print(f"  Duplicates removed:{clean_report['duplicate_rows_removed_by_post_id']}")
    print(f"  Interim output:    {interim_out}")
    print(f"  Processed output:  {proc_out / 'standardized_data.csv'}")

    return standardized

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CoordinX Ingestion Pipeline (Phase 1)")
    parser.add_argument("--input", required=True, help="Path to raw CSV")
    parser.add_argument("--interim-dir", default="data/interim")
    parser.add_argument("--processed-dir", default="data/processed")
    args = parser.parse_args()

    run_ingest(args.input, args.interim_dir, args.processed_dir)
