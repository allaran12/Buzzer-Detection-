import unittest
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np
import pandas as pd

from src.inference.model_adapter import ModelAdapter
from src.inference.model_registry import ModelConfig


class ClassProbabilityTests(unittest.TestCase):
    def test_probability_uses_class_one_label(self):
        adapter = ModelAdapter(SimpleNamespace(experiment="proxy", version="test"))
        adapter._model = type("Classifier", (), {
            "predict": lambda self, features: np.array([1]),
            "predict_proba": lambda self, features: np.array([[0.8, 0.2]]),
            "classes_": np.array([1, 0]),
        })()
        result = adapter.predict(pd.DataFrame({"x": [1]}))
        self.assertEqual(result.probability_buzzer, [0.8])


if __name__ == "__main__":
    unittest.main()
