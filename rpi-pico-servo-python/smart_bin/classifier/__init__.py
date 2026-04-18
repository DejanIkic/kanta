"""Classifier abstraction layer for waste classification."""

from .base import IClassifier, Prediction
from .mock_classifier import MockClassifier

__all__ = ["IClassifier", "Prediction", "MockClassifier"]

# Lazy import: TFLiteClassifier only available if tflite-runtime is installed
try:
    from .tflite_classifier import TFLiteClassifier
    __all__.append("TFLiteClassifier")
except ImportError:
    pass
