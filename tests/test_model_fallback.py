import unittest
from types import SimpleNamespace
from unittest.mock import patch

import pandas as pd

from src.inference.model_adapter import ModelAdapter


class ModelFallbackTests(unittest.TestCase):
    def test_final_model_falls_back_to_available_proxy_without_torch(self):
        config = SimpleNamespace(
            experiment="final",
            path=None,
            version="test",
            final_dir=None,
        )
        adapter = ModelAdapter(config)
        with patch("src.inference.model_adapter.validate_model_config"), patch("src.inference.model_adapter.ModelAdapter._load_final", side_effect=RuntimeError("Final models require torch")):
            with patch("src.inference.model_adapter.ModelAdapter._load_proxy_fallback") as fallback:
                adapter.load()
        fallback.assert_called_once()

    def test_final_artifact_error_uses_trained_compatibility_proxy(self):
        config = SimpleNamespace(
            experiment="final",
            path=None,
            version="test",
            final_dir=None,
        )
        adapter = ModelAdapter(config)
        with patch("src.inference.model_adapter.validate_model_config"), patch(
            "src.inference.model_adapter.ModelAdapter._load_final",
            side_effect=ValueError("_fill_dtype is unavailable"),
        ), patch(
            "src.inference.model_adapter.ModelAdapter._load_compatibility_proxy",
            return_value=True,
        ) as compatibility_proxy:
            adapter.load()

        compatibility_proxy.assert_called_once()


if __name__ == "__main__":
    unittest.main()
