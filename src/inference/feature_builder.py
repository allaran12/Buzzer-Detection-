from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

try:
    from models.phase6_advanced import MODEL_FEATURES
except ModuleNotFoundError:
    from src.models.phase6_advanced import MODEL_FEATURES


@dataclass(frozen=True)
class FeatureBatch:
    frame: pd.DataFrame
    path: Path


def validate_feature_frame(frame: pd.DataFrame) -> pd.DataFrame:
    missing = [column for column in ["account_id", "username", "text_blob", *MODEL_FEATURES] if column not in frame.columns]
    if missing:
        raise ValueError(f"Feature dataset is missing required columns: {', '.join(missing)}")
    return frame


def load_feature_batch(path: str | Path, root: Path) -> FeatureBatch:
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = root / candidate
    candidate = candidate.resolve()
    data_root = (root / "data").resolve()
    try:
        candidate.relative_to(data_root)
    except ValueError as exc:
        raise ValueError("Feature dataset must be inside the data directory") from exc
    if not candidate.exists():
        raise FileNotFoundError(f"Feature dataset does not exist: {candidate}")
    frame = pd.read_csv(candidate, dtype={"account_id": "string", "username": "string", "text_blob": "string"})
    validate_feature_frame(frame)
    return FeatureBatch(frame=frame, path=candidate)
