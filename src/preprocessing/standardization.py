"""
Input : data/interim/cleaned_data.csv
Output: data/processed/standardized_data.csv
        data/processed/standardization_report.txt
Install:
    pip install pandas
Run:
    python src/preprocessing/standardization.py
    python src/preprocessing/standardization.py --input data/interim/cleaned_data.csv
"""
from pathlib import Path
import argparse
import ast
import json
import pandas as pd

ID_COLUMNS = [
    "post_id", "account_id", "id", "user_id",
    "source_post_id", "source_account_id",
    "target_post_id", "target_account_id", "conversation_id",
]
DATE_COLUMNS = ["date", "created"]
NUMERIC_COLUMNS = ["followers", "following", "statuses"]
BOOLEAN_COLUMNS = ["is_rt", "is_reply", "is_quote"]

def parse_bool(value):
    if pd.isna(value):
        return pd.NA
    if isinstance(value, bool):
        return value
    value = str(value).strip().lower()
    if value in {"true", "1", "yes", "y"}:
        return True
    if value in {"false", "0", "no", "n"}:
        return False
    return pd.NA

def parse_mentions(value):
    """Convert list-like mention data to a consistent JSON array string."""
    if pd.isna(value) or str(value).strip() == "":
        return "[]"
    if isinstance(value, list):
        parsed = value
    else:
        raw = str(value).strip()
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            try:
                parsed = ast.literal_eval(raw)
            except (ValueError, SyntaxError):
                return "[]"
    if not isinstance(parsed, (list, tuple)):
        return "[]"
    result = []
    seen = set()
    for item in parsed:
        if item is None:
            continue
        item = str(item).strip()
        if item and item not in seen:
            result.append(item)
            seen.add(item)
    return json.dumps(result, ensure_ascii=False)

def standardize_dataset(df: pd.DataFrame):
    df = df.copy()
    report = {}

    for col in ID_COLUMNS:
        if col in df.columns:
            df[col] = df[col].astype("string").str.strip()
            df[col] = df[col].replace("", pd.NA)

    for col in DATE_COLUMNS:
        if col in df.columns:
            parsed = pd.to_datetime(df[col], errors="coerce", utc=True)
            report[f"{col}_invalid_or_missing_after_parse"] = int(parsed.isna().sum())
            df[col] = parsed

    for col in NUMERIC_COLUMNS:
        if col in df.columns:
            numeric = pd.to_numeric(df[col], errors="coerce")
            non_integer = numeric.notna() & (numeric % 1 != 0)
            if non_integer.any():
                report[f"{col}_non_integer_values"] = int(non_integer.sum())
            df[col] = numeric.round().astype("Int64")

    for col in BOOLEAN_COLUMNS:
        if col in df.columns:
            df[col] = df[col].map(parse_bool).astype("boolean")

    if "text" in df.columns:
        df["text"] = (
            df["text"].astype("string")
            .str.replace("\r\n", "\n", regex=False)
            .str.replace("\r", "\n", regex=False)
            .str.strip()
        )

    for col in ["username", "target_username", "relation_type", "isu"]:
        if col in df.columns:
            df[col] = df[col].astype("string").str.strip()

    if "mentioned_user_ids" in df.columns:
        df["mentioned_user_ids"] = df["mentioned_user_ids"].map(parse_mentions).astype("string")

    report["rows"] = len(df)
    report["columns"] = len(df.columns)
    report["relation_type_counts"] = (
        df["relation_type"].value_counts(dropna=False).to_dict()
        if "relation_type" in df.columns else {}
    )
    report["retweet_rows"] = (
        int(df["is_rt"].fillna(False).sum()) if "is_rt" in df.columns else "column_not_found"
    )
    return df, report

def main():
    parser = argparse.ArgumentParser(description="Standardisasi dataset CoordinX")
    parser.add_argument("--input", default="data/interim/cleaned_data.csv")
    parser.add_argument("--output-dir", default="data/processed")
    args = parser.parse_args()

    input_path = Path(args.input)
    file_stem = input_path.stem.replace("_cleaned", "")
    output_dir = Path("data/processed") / file_stem
    output_dir.mkdir(parents=True, exist_ok=True)

    if not input_path.exists():
        raise FileNotFoundError(
            f"File tidak ditemukan: {input_path}\n"
            "Jalankan cleaning.py terlebih dahulu."
        )

    df = pd.read_csv(input_path, dtype="string", keep_default_na=True)
    standardized, report = standardize_dataset(df)

    standardized.to_csv(
        output_dir / "standardized_data.csv",
        index=False,
        encoding="utf-8-sig",
        date_format="%Y-%m-%dT%H:%M:%SZ",
    )

    lines = ["COORDINX - DATA STANDARDIZATION REPORT", "=" * 42]
    for key, value in report.items():
        lines.append(f"{key}: {value}")
    (output_dir / "standardization_report.txt").write_text(
        "\n".join(lines), encoding="utf-8"
    )
    print("\n".join(lines))
    print(f"\nOutput tersimpan di: {output_dir.resolve()}")

if __name__ == "__main__":
    main()
