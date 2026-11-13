import unittest
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np
import pandas as pd

from src.inference.model_adapter import ModelAdapter


class HeuristicFallbackTests(unittest.TestCase):
    def test_incompatible_sklearn_artifact_returns_safe_fallback(self):
        adapter = ModelAdapter(SimpleNamespace(experiment="proxy", version="test"))
        adapter._model = type("Classifier", (), {
            "predict": lambda self, features: (_ for _ in ()).throw(AttributeError("_fill_dtype")),
            "predict_proba": lambda self, features: (_ for _ in ()).throw(AttributeError("_fill_dtype")),
        })()
        result = adapter.predict(pd.DataFrame({"feature": [1.0, 2.0]}))
        self.assertEqual(len(result.probability_buzzer), 2)
        self.assertTrue(adapter._heuristic_fallback)


if __name__ == "__main__":
    unittest.main()
