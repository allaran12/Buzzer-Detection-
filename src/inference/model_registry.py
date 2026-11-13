from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ModelConfig:
    experiment: str
    path: Path
    version: str
    final_dir: Path | None = None


def repository_root() -> Path:
    return Path(__file__).resolve().parents[2]


def get_model_config(root: Path | None = None) -> ModelConfig:
    root = (root or repository_root()).resolve()
    experiment = os.getenv("COORDINX_MODEL_EXPERIMENT", "final")
    configured_path = os.getenv("COORDINX_MODEL_PATH")
    if experiment == "final":
        final_dir = Path(os.getenv("COORDINX_FINAL_MODEL_DIR", root / "models" / "final"))
        path = Path(configured_path) if configured_path else final_dir / "indobertweet_final.pkl"
        if not path.is_absolute():
            path = root / path
        version = os.getenv("COORDINX_MODEL_VERSION", "coordinx-final-v1.0.0")
        return ModelConfig(experiment, path.resolve(), version, final_dir.resolve())
    path = Path(configured_path) if configured_path else root / "models" / f"phase6_fusion_proxy_{experiment}_canonical.pkl"
    if not path.is_absolute():
        path = root / path
    return ModelConfig(experiment, path.resolve(), os.getenv("COORDINX_MODEL_VERSION", f"phase6-{experiment}-canonical"))


def validate_model_config(config: ModelConfig, root: Path | None = None) -> None:
    root = (root or repository_root()).resolve()
    if config.experiment == "final":
        if config.final_dir is None or not config.final_dir.is_dir():
            raise FileNotFoundError(f"Final model directory does not exist: {config.final_dir}")
        required = ("indobertweet_final.pkl", "temporal_lstm_final.pt", "graphsage_final.pt")
        missing = [name for name in required if not (config.final_dir / name).exists()]
        if missing:
            raise FileNotFoundError(f"Final model artifacts missing: {', '.join(missing)}")
        return
    if not config.path.exists():
        raise FileNotFoundError(f"Configured model does not exist: {config.path}")
    try:
        config.path.relative_to(root)
    except ValueError as exc:
        raise ValueError("Model path must be inside the repository") from exc
