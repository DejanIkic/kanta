"""
Abstract base class for waste classifiers.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict

import numpy as np


@dataclass
class Prediction:
    """Result from a classification prediction."""
    waste_type: str
    confidence: float
    angle: int
    all_scores: Dict[str, float] = field(default_factory=dict)


class IClassifier(ABC):
    """Interface for waste classifiers."""

    @abstractmethod
    def load_model(self) -> None:
        """Load the model and labels into memory."""
        ...

    @abstractmethod
    def predict(self, image: np.ndarray) -> Prediction:
        """
        Classify an image.

        :param image: Input image as numpy array (H, W, C) in BGR or RGB format.
        :return: Prediction with waste type, confidence, angle, and all scores.
        """
        ...

    @property
    @abstractmethod
    def is_loaded(self) -> bool:
        """Whether the model has been loaded successfully."""
        ...
