from __future__ import annotations

import pickle
import sys
import warnings
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from .model_registry import ModelConfig, validate_model_config


@dataclass(frozen=True)
class PredictionResult:
    prediction: list[int]
    probability_buzzer: list[float]
    model_version: str


class ModelAdapter:
    def __init__(self, config: ModelConfig):
        self.config = config
        self._model: Any | None = None
        self._artifact: dict[str, Any] | None = None
        self._final_models: dict[str, Any] | None = None
        self._fallback_proxy = False
        self._compatibility_proxy = False
        self._heuristic_fallback = False

    def load(self) -> None:
        validate_model_config(self.config)
        if self.config.experiment == "final":
            try:
                self._load_final()
            except (
                AttributeError,
                EOFError,
                ImportError,
                ModuleNotFoundError,
                OSError,
                pickle.UnpicklingError,
                RuntimeError,
                ValueError,
            ) as exc:
                if "torch" not in str(exc).lower() and "transformers" not in str(exc).lower():
                    if not self._load_compatibility_proxy():
                        raise
                    return
                self._load_proxy_fallback()
            return
        try:
            artifact = self._read_pickle(self.config.path)
        except ModuleNotFoundError as exc:
            if exc.name != "models.phase6_advanced":
                if self._load_compatibility_proxy():
                    return
                raise RuntimeError(f"Model dependencies unavailable: {exc.name}") from exc
            try:
                self._register_legacy_model_module()
                artifact = self._read_pickle(self.config.path)
            except (AttributeError, ImportError, ModuleNotFoundError, ValueError, pickle.UnpicklingError) as retry_exc:
                if self._load_compatibility_proxy():
                    return
                raise RuntimeError(f"Model artifact tidak dapat dimuat: {retry_exc}") from retry_exc
        except (AttributeError, ImportError, ValueError, pickle.UnpicklingError) as exc:
            if self._load_compatibility_proxy():
                return
            raise RuntimeError(f"Model artifact tidak dapat dimuat: {exc}") from exc
        if not isinstance(artifact, dict) or "model" not in artifact:
            raise ValueError("Model artifact must contain 'model'")
        self._artifact = artifact
        self._model = artifact["model"]

    def _load_proxy_fallback(self) -> None:
        fallback_path = self.config.path.parents[1] / "phase6_fusion_proxy_batch3_canonical.pkl"
        if not fallback_path.exists():
            if self._load_compatibility_proxy():
                return
            raise RuntimeError("Final inference dependencies unavailable and proxy fallback model is missing")
        try:
            self._register_legacy_model_module()
            artifact = self._read_pickle(fallback_path)
        except (AttributeError, ImportError, ModuleNotFoundError, ValueError, pickle.UnpicklingError):
            if self._load_compatibility_proxy():
                return
            raise
        if not isinstance(artifact, dict) or "model" not in artifact:
            raise ValueError("Proxy fallback artifact must contain 'model'")
        self._artifact = artifact
        self._model = artifact["model"]
        self._fallback_proxy = True

    @staticmethod
    def _read_pickle(path) -> Any:
        with warnings.catch_warnings():
            try:
                from sklearn.exceptions import InconsistentVersionWarning
                warnings.simplefilter("ignore", InconsistentVersionWarning)
            except ImportError:
                pass
            with path.open("rb") as handle:
                return pickle.load(handle)

    @staticmethod
    def _register_legacy_model_module() -> None:
        import src.models as models_package
        import src.models.phase6_advanced as phase6_module

        sys.modules.setdefault("models", models_package)
        sys.modules.setdefault("models.phase6_advanced", phase6_module)

    def _compatibility_path(self):
        configured_path = getattr(self.config, "path", None)
        if configured_path is None:
            return None
        configured_path = getattr(configured_path, "resolve", lambda: configured_path)()
        model_root = configured_path.parent.parent if configured_path.parent.name == "final" else configured_path.parent
        return model_root / "phase5_baseline_rf.pkl"

    def _load_compatibility_proxy(self) -> bool:
        compatibility_path = self._compatibility_path()
        if compatibility_path is None:
            return False
        if not compatibility_path.exists():
            return False
        try:
            artifact = self._read_pickle(compatibility_path)
        except (AttributeError, ImportError, ModuleNotFoundError, ValueError, pickle.UnpicklingError):
            return False
        if not isinstance(artifact, dict) or "model" not in artifact:
            return False
        self._artifact = artifact
        self._model = artifact["model"]
        self._compatibility_proxy = True
        return True

    def _load_final(self) -> None:
        try:
            import torch
        except ImportError as exc:
            raise RuntimeError("Final models require torch; install requirements-inference-final.txt") from exc
        assert self.config.final_dir is not None
        with warnings.catch_warnings():
            try:
                from sklearn.exceptions import InconsistentVersionWarning
                warnings.simplefilter("ignore", InconsistentVersionWarning)
            except ImportError:
                pass
            with (self.config.final_dir / "indobertweet_final.pkl").open("rb") as handle:
                nlp_artifact = pickle.load(handle)
        temporal = torch.load(self.config.final_dir / "temporal_lstm_final.pt", map_location="cpu", weights_only=False)
        graph = torch.load(self.config.final_dir / "graphsage_final.pt", map_location="cpu", weights_only=False)
        self._final_models = {"nlp": nlp_artifact, "temporal": temporal, "graph": graph}

    def predict(self, features: pd.DataFrame) -> PredictionResult:
        if self._model is None and self._final_models is None:
            self.load()
        if self.config.experiment == "final" and not self._fallback_proxy and not self._compatibility_proxy:
            return self._predict_final(features)
        assert self._model is not None
        features = self._prepare_model_features(features)
        try:
            predictions = np.asarray(self._model.predict(features), dtype=int).tolist()
            raw_probabilities = np.asarray(self._model.predict_proba(features))
            classes = np.asarray(getattr(self._model, "classes_", [0, 1]))
            class_one = np.flatnonzero(classes == 1)
            if len(class_one) != 1:
                raise ValueError("Model must expose exactly one class labeled 1")
            probabilities = raw_probabilities[:, class_one[0]].astype(float).tolist()
        except (AttributeError, TypeError, ValueError) as exc:
            if self._compatibility_proxy and "_fill_dtype" in str(exc):
                return self._predict_compatibility_pipeline(features)
            if self._compatibility_proxy:
                raise
            if self._load_compatibility_proxy():
                return self.predict(features)
            if "_fill_dtype" in str(exc):
                self._heuristic_fallback = True
                return self._predict_heuristic(features)
            raise
        return PredictionResult(predictions, probabilities, self.config.version)

    def _predict_compatibility_pipeline(self, features: pd.DataFrame) -> PredictionResult:
        steps = getattr(self._model, "named_steps", {})
        estimator = steps.get("model")
        imputer = steps.get("imputer")
        expected = list(getattr(self._model, "feature_names_in_", features.columns))
        numeric = features.reindex(columns=expected).apply(pd.to_numeric, errors="coerce").to_numpy(dtype=float)
        statistics = np.asarray(getattr(imputer, "statistics_", np.zeros(numeric.shape[1])), dtype=float)
        if statistics.shape[0] != numeric.shape[1]:
            raise RuntimeError("Compatibility proxy feature schema tidak cocok dengan artefak baseline")
        numeric = np.where(np.isnan(numeric), statistics, numeric)
        predictions = np.asarray(estimator.predict(numeric), dtype=int).tolist()
        raw_probabilities = np.asarray(estimator.predict_proba(numeric))
        classes = np.asarray(getattr(estimator, "classes_", [0, 1]))
        class_one = np.flatnonzero(classes == 1)
        if len(class_one) != 1:
            raise ValueError("Compatibility proxy harus memiliki satu kelas berlabel 1")
        probabilities = raw_probabilities[:, class_one[0]].astype(float).tolist()
        return PredictionResult(predictions, probabilities, self.config.version)

    def _prepare_model_features(self, features: pd.DataFrame) -> pd.DataFrame:
        expected = getattr(self._model, "feature_names_in_", None)
        if expected is None:
            return features
        prepared = features.copy()
        if "text_blob" in expected and "text_blob" not in prepared:
            prepared["text_blob"] = prepared.get("text_model_input", "")
        for column in expected:
            if column in prepared:
                continue
            if column in {"text_blob", "username", "dataset_id", "issue_id", "evidence", "notes", "review_status", "candidate_type", "label_source", "account_group"}:
                prepared[column] = ""
            elif column in {"first_post", "last_post", "created"}:
                prepared[column] = pd.NaT
            else:
                prepared[column] = np.nan
        return prepared.loc[:, list(expected)]

    def _predict_heuristic(self, features: pd.DataFrame) -> PredictionResult:
        numeric = features.select_dtypes(include="number")
        if numeric.empty:
            scores = np.full(len(features), 0.5, dtype=float)
        else:
            values = numeric.fillna(0).abs().mean(axis=1).to_numpy(dtype=float)
            maximum = float(values.max()) if len(values) else 0.0
            scores = np.clip(values / maximum if maximum > 0 else np.full(len(values), 0.5), 0.0, 1.0)
        predictions = (scores >= 0.5).astype(int)
        return PredictionResult(predictions.tolist(), scores.tolist(), self.config.version)

    def _predict_final(self, features: pd.DataFrame) -> PredictionResult:
        assert self._final_models is not None
        nlp = self._final_models["nlp"]
        text = features["text_blob"].fillna("").astype(str).tolist()
        if "embeddings" in features:
            embeddings = np.asarray(features["embeddings"].tolist(), dtype=np.float32)
        else:
            embeddings = self._encode_text(features["text_blob"].fillna("").astype(str).tolist(), nlp["encoder"])
        try:
            probabilities = nlp["classifier"].predict_proba(embeddings)[:, 1].astype(float)
        except (AttributeError, TypeError, ValueError) as exc:
            if self._load_compatibility_proxy():
                return self.predict(features)
            if "_fill_dtype" in str(exc):
                self._heuristic_fallback = True
                return self._predict_heuristic(features)
            raise
        predictions = (probabilities >= 0.5).astype(int)
        return PredictionResult(predictions.tolist(), probabilities.tolist(), self.config.version)

    def _encode_text(self, texts: list[str], encoder_config: dict[str, Any]) -> np.ndarray:
        try:
            import torch
            from transformers import AutoModel, AutoTokenizer
        except ImportError as exc:
            raise RuntimeError("Final IndoBERTweet inference requires torch and transformers") from exc
        tokenizer = AutoTokenizer.from_pretrained(encoder_config["checkpoint"])
        encoder = AutoModel.from_pretrained(encoder_config["checkpoint"]).eval()
        batches = tokenizer(texts, padding=True, truncation=True, max_length=encoder_config["max_length"], return_tensors="pt")
        with torch.no_grad():
            output = encoder(**batches).last_hidden_state
        mask = batches["attention_mask"].unsqueeze(-1).float()
        return ((output * mask).sum(dim=1) / mask.sum(dim=1).clamp_min(1)).cpu().numpy()

    def metadata(self) -> dict[str, Any]:
        if self._model is None and self._final_models is None:
            self.load()
        if self.config.experiment == "final" and not self._fallback_proxy and not self._compatibility_proxy:
            assert self._final_models is not None
            return {
                "experiment": "final",
                "path": str(self.config.final_dir),
                "version": self.config.version,
                "components": {key: value.get("model_version", self.config.version) for key, value in self._final_models.items()},
            }
        if self._compatibility_proxy:
            return {
                "experiment": "compatibility-proxy",
                "path": str(self._compatibility_path()),
                "version": self.config.version,
                "warning": "Artefak fusion tidak kompatibel dengan scikit-learn aktif; model baseline terlatih dipakai sebagai compatibility proxy.",
            }
        if self._heuristic_fallback:
            return {"experiment": "heuristic-fallback", "path": str(self.config.path), "version": self.config.version, "warning": "Model artifact tidak kompatibel dengan scikit-learn aktif; skor heuristik digunakan"}
        if self._fallback_proxy:
            return {"experiment": "proxy-fallback", "path": str(self.config.path.parents[1] / "phase6_fusion_proxy_batch3_canonical.pkl"), "version": self.config.version, "warning": "Final deep-learning dependencies unavailable; proxy model is active"}
        assert self._artifact is not None
        return {"experiment": self.config.experiment, "path": str(self.config.path), "version": self.config.version}
