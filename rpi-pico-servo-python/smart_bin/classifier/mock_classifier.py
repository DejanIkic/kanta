"""
Mock classifier for development without a real model.
Returns random predictions with configurable waste types.
"""

import random
from typing import Dict

import numpy as np

from .base import IClassifier, Prediction

WASTE_TYPES = ["plastic", "glass", "pet", "organic", "other"]

# Default angles matching config waste_angles
DEFAULT_ANGLES = {
    "plastic": -20,
    "glass": 20,
    "pet": -20,
    "organic": 20,
    "other": 0,
}


class MockClassifier(IClassifier):
    """Mock classifier that returns random predictions for testing."""

    def __init__(self, waste_types: list = None, angles: dict = None):
        self._waste_types = waste_types or WASTE_TYPES
        self._angles = angles or DEFAULT_ANGLES
        self._loaded = False

    def load_model(self) -> None:
        """No-op for mock - just mark as loaded."""
        self._loaded = True

    def predict(self, image: np.ndarray) -> Prediction:
        """
        Return a random prediction.

        :param image: Input image (ignored in mock).
        :return: Random Prediction.
        """
        if not self._loaded:
            raise RuntimeError("Model not loaded. Call load_model() first.")

        # Generate random scores that sum to ~1.0
        raw_scores = [random.random() for _ in self._waste_types]
        total = sum(raw_scores)
        scores = {wt: s / total for wt, s in zip(self._waste_types, raw_scores)}

        # Pick the highest score as prediction
        best_type = max(scores, key=scores.get)
        confidence = scores[best_type]
        angle = self._angles.get(best_type, 0)

        return Prediction(
            waste_type=best_type,
            confidence=round(confidence, 4),
            angle=angle,
            all_scores={k: round(v, 4) for k, v in scores.items()},
        )

    @property
    def is_loaded(self) -> bool:
        return self._loaded
