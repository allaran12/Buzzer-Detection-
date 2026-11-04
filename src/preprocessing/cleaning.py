"""
Input : data/raw/prayforkalimantan.csv
Output: data/interim/cleaned_data.csv
        data/interim/duplicate_posts.csv
        data/interim/rejected_rows.csv
        data/interim/cleaning_report.txt

Install:
    pip install pandas
Run:
    python src/preprocessing/cleaning.py
    python src/preprocessing/cleaning.py --input data/raw/nama_file.csv
"""

from pathlib import Path
import argparse
import pandas as pd

REQUIRED_COLUMNS = [
    "post_id", "account_id", "date", "text", "username",
    "relation_type", "is_rt", "is_reply", "is_quote",
]

def read_csv_safely(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype="string", keep_default_na=True)

def clean_dataset(df: pd.DataFrame):
    df = df.copy()
    initial_rows = len(df)

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

    duplicate_mask = valid.duplicated(subset=["post_id"], keep="first")
    duplicates = valid.loc[duplicate_mask].copy()
    cleaned = valid.loc[~duplicate_mask].copy()
    
    report = {
        "rows_before": initial_rows,
        "rows_rejected_empty_text_or_missing_identity": len(rejected),
        "duplicate_rows_removed_by_post_id": len(duplicates),
        "rows_after_cleaning": len(cleaned),
        "unique_post_ids_after_cleaning": cleaned["post_id"].nunique(dropna=True),
        "unique_accounts_after_cleaning": cleaned["account_id"].nunique(dropna=True),
        "missing_bio_after_cleaning": int(cleaned["bio"].isna().sum()) if "bio" in cleaned else "column_not_found",
        "relation_type_counts": cleaned["relation_type"].value_counts(dropna=False).to_dict(),
    }
    return cleaned, duplicates, rejected, report

def main():
    parser = argparse.ArgumentParser(description="Cleaning dataset CoordinX")
    parser.add_argument("--input", default="data/raw/prayforkalimantan.csv")
    parser.add_argument("--output-dir", default="data/interim")
    args = parser.parse_args()

    input_path = Path(args.input)
    file_stem = input_path.stem
    output_dir = Path("data/interim") / file_stem
    output_dir.mkdir(parents=True, exist_ok=True)

    if not input_path.exists():
        raise FileNotFoundError(
            f"File tidak ditemukan: {input_path}\n"
            "Letakkan CSV mentah di data/raw/ atau gunakan --input."
        )

    raw = read_csv_safely(input_path)
    cleaned, duplicates, rejected, report = clean_dataset(raw)

    cleaned.to_csv(output_dir / f"{file_stem}_cleaned.csv", index=False, encoding="utf-8-sig")
    duplicates.to_csv(output_dir / f"{file_stem}_duplicates.csv", index=False, encoding="utf-8-sig")
    rejected.to_csv(output_dir / f"{file_stem}_rejected.csv", index=False, encoding="utf-8-sig")

    lines = ["COORDINX - DATA CLEANING REPORT", "=" * 36]
    for key, value in report.items():
        lines.append(f"{key}: {value}")
    (output_dir / f"{file_stem}_report.txt").write_text("\n".join(lines), encoding="utf-8")

    print("\n".join(lines))
    print(f"\nOutput tersimpan di: {output_dir.resolve()}")

if __name__ == "__main__":
    main()
