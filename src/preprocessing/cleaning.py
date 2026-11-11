"""
Data Cleaning & Ingestion for CoordinX (PRD Phase 1)
Input : data/raw/{dataset}.csv
Output: data/interim/{dataset}/{dataset}_cleaned.csv
        data/interim/{dataset}/{dataset}_duplicates.csv
        data/interim/{dataset}/{dataset}_rejected.csv
        data/interim/{dataset}/{dataset}_report.txt
"""
from pathlib import Path
import argparse
import pandas as pd

COLUMN_ALIASES = {
    "id": "post_id",
    "tweet_id": "post_id",
    "user_id": "account_id",
    "author_id": "account_id",
    "created_at": "date",
    "timestamp": "date",
    "content": "text",
    "tweet": "text",
    "full_text": "text",
    "screen_name": "username",
    "user_name": "username",
}

REQUIRED_COLUMNS = [
    "post_id", "account_id", "date", "text", "username",
    "relation_type", "is_rt", "is_reply", "is_quote",
]

def read_csv_safely(path: Path) -> pd.DataFrame:
    # PRD FR-04: ID wajib dibaca sebagai string, bukan float
    return pd.read_csv(path, dtype="string", keep_default_na=True)

def apply_column_mapping(df: pd.DataFrame) -> pd.DataFrame:
    # PRD FR-02: Column mapping untuk menangani variasi format scraper
    mapping = {c: COLUMN_ALIASES[c] for c in df.columns if c in COLUMN_ALIASES and COLUMN_ALIASES[c] not in df.columns}
    return df.rename(columns=mapping)

def clean_dataset(df: pd.DataFrame, default_isu: str = "unknown"):
    df = apply_column_mapping(df.copy())
    initial_rows = len(df)

    # Fallback jika isu tidak ada di CSV
    if "isu" not in df.columns:
        df["isu"] = default_isu

    # Fallback boolean relations jika kosong
    for col in ["is_rt", "is_reply", "is_quote"]:
        if col not in df.columns:
            df[col] = "False"

    # Fallback relation_type jika kosong
    if "relation_type" not in df.columns:
        df["relation_type"] = "original"

    missing_columns = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing_columns:
        raise ValueError(f"Kolom wajib tidak ditemukan: {missing_columns}")

    for col in ["post_id", "account_id", "username", "relation_type"]:
        df[col] = df[col].astype("string").str.strip()

    df["text"] = df["text"].astype("string")
    empty_text = df["text"].isna() | df["text"].str.strip().eq("")
    missing_identity = (
        df["post_id"].isna() | df["post_id"].eq("") |
        df["account_id"].isna() | df["account_id"].eq("")
    )
    rejected_mask = empty_text | missing_identity
    rejected = df.loc[rejected_mask].copy()
    valid = df.loc[~rejected_mask].copy()

    # PRD FR-05: Deduplikasi hanya berdasarkan post_id, jangan buang teks serupa
    duplicate_mask = valid.duplicated(subset=["post_id"], keep="first")
    duplicates = valid.loc[duplicate_mask].copy()
    cleaned = valid.loc[~duplicate_mask].copy()

    # PRD: Audit relasi (reply/quote yang kehilangan target)
    replies_quotes = cleaned[cleaned["relation_type"].isin(["reply", "quote"])]
    missing_target = (
        replies_quotes["target_account_id"].isna().sum()
        if "target_account_id" in replies_quotes else len(replies_quotes)
    )

    report = {
        "rows_before": initial_rows,
        "rows_rejected_empty_text_or_missing_identity": len(rejected),
        "duplicate_rows_removed_by_post_id": len(duplicates),
        "rows_after_cleaning": len(cleaned),
        "unique_post_ids_after_cleaning": cleaned["post_id"].nunique(dropna=True),
        "unique_accounts_after_cleaning": cleaned["account_id"].nunique(dropna=True),
        "relation_type_counts": cleaned["relation_type"].value_counts(dropna=False).to_dict(),
        "interactions_with_missing_target_account": int(missing_target),
    }
    return cleaned, duplicates, rejected, report

def main():
    parser = argparse.ArgumentParser(description="Cleaning & Ingestion CoordinX (PRD Phase 1)")
    parser.add_argument("--input", required=True, help="Path ke CSV raw")
    parser.add_argument("--output-dir", default="data/interim")
    args = parser.parse_args()

    input_path = Path(args.input)
    file_stem = input_path.stem
    output_dir = Path(args.output_dir) / file_stem
    output_dir.mkdir(parents=True, exist_ok=True)

    if not input_path.exists():
        raise FileNotFoundError(f"File tidak ditemukan: {input_path}")

    raw = read_csv_safely(input_path)
    cleaned, duplicates, rejected, report = clean_dataset(raw, default_isu=file_stem)

    cleaned.to_csv(output_dir / f"{file_stem}_cleaned.csv", index=False, encoding="utf-8-sig")
    duplicates.to_csv(output_dir / f"{file_stem}_duplicates.csv", index=False, encoding="utf-8-sig")
    rejected.to_csv(output_dir / f"{file_stem}_rejected.csv", index=False, encoding="utf-8-sig")

    lines = ["COORDINX - DATA CLEANING & AUDIT REPORT", "=" * 40]
    for key, value in report.items():
        lines.append(f"{key}: {value}")
    (output_dir / f"{file_stem}_report.txt").write_text("\n".join(lines), encoding="utf-8")

    print("\n".join(lines))
    print(f"\n✓ Output tersimpan di: {output_dir.resolve()}")

if __name__ == "__main__":
    main()
