"""
TFLite waste classifier implementation.
"""

import os
from typing import Dict, List

import numpy as np

from .base import IClassifier, Prediction

try:
    import tflite_runtime.interpreter as tflite
except ImportError:
    tflite = None


class TFLiteClassifier(IClassifier):
    """Classifier using TFLite runtime for inference."""

    def __init__(self, model_path: str, labels_path: str, waste_angles: dict = None):
        self._model_path = model_path
        self._labels_path = labels_path
        self._waste_angles = waste_angles or {}
        self._interpreter = None
        self._input_details = None
        self._output_details = None
        self._labels: List[str] = []
        self._loaded = False

    def load_model(self) -> None:
        """Load TFLite model and labels."""
        if tflite is None:
            raise ImportError(
                "tflite-runtime not installed. Install with: "
                "pip install tflite-runtime"
            )

        if not os.path.exists(self._model_path):
            raise FileNotFoundError(f"Model file not found: {self._model_path}")

        if not os.path.exists(self._labels_path):
            raise FileNotFoundError(f"Labels file not found: {self._labels_path}")

        # Load labels
        with open(self._labels_path, "r") as f:
            self._labels = [line.strip() for line in f.readlines() if line.strip()]

        # Load interpreter
        self._interpreter = tflite.Interpreter(model_path=self._model_path)
        self._interpreter.allocate_tensors()

        self._input_details = self._interpreter.get_input_details()
        self._output_details = self._interpreter.get_output_details()

        self._loaded = True

    def predict(self, image: np.ndarray) -> Prediction:
        """
        Run TFLite inference on image.

        :param image: Input image as numpy array (H, W, C), uint8.
        :return: Prediction result.
        """
        if not self._loaded:
            raise RuntimeError("Model not loaded. Call load_model() first.")

        # Get expected input shape
        input_shape = self._input_details[0]["shape"]  # [1, H, W, C]
        _, h, w, c = input_shape

        # Preprocess: resize + normalize
        img = self._preprocess(image, h, w)

        # Run inference
        self._interpreter.set_tensor(self._input_details[0]["index"], img)
        self._interpreter.invoke()

        # Get output
        output_data = self._interpreter.get_tensor(self._output_details[0]["index"])
        scores = output_data[0]  # First batch

        # Build score dict
        all_scores: Dict[str, float] = {}
        for i, label in enumerate(self._labels):
            all_scores[label] = round(float(scores[i]), 4)

        # Best prediction
        best_idx = int(np.argmax(scores))
        best_type = self._labels[best_idx]
        confidence = float(scores[best_idx])
        angle = self._waste_angles.get(best_type, {}).get("horizontal", 0)

        return Prediction(
            waste_type=best_type,
            confidence=round(confidence, 4),
            angle=angle,
            all_scores=all_scores,
        )

    def _preprocess(self, image: np.ndarray, target_h: int, target_w: int) -> np.ndarray:
        """
        Preprocess image for TFLite model input.

        :param image: Raw image (H, W, C), uint8.
        :param target_h: Target height.
        :param target_w: Target width.
        :return: Preprocessed image [1, H, W, C], float32.
        """
        try:
            import cv2
            img = cv2.resize(image, (target_w, target_h))
        except ImportError:
            # Fallback: naive resize via numpy if cv2 unavailable
            img = self._simple_resize(image, target_h, target_w)

        # Normalize to [0, 1] or [-1, 1] depending on model
        img = img.astype(np.float32)
        # Most TFLite image models expect [0, 1] or [-1, 1]
        # Check input quantization - if uint8 input, no normalize needed
        input_dtype = self._input_details[0]["dtype"]
        if input_dtype == np.uint8:
            img = img.astype(np.uint8)
        else:
            img = img / 255.0

        # Add batch dimension
        img = np.expand_dims(img, axis=0)

        return img

    @staticmethod
    def _simple_resize(image: np.ndarray, target_h: int, target_w: int) -> np.ndarray:
        """Naive resize via slicing when cv2 unavailable."""
        h, w = image.shape[:2]
        # Simple stride-based resize
        step_h = max(1, h // target_h)
        step_w = max(1, w // target_w)
        img = image[::step_h, ::step_w][:target_h, :target_w]
        # Pad if too small
        pad_h = target_h - img.shape[0]
        pad_w = target_w - img.shape[1]
        if pad_h > 0 or pad_w > 0:
            img = np.pad(img, ((0, pad_h), (0, pad_w), (0, 0)), mode="edge")
        return img[:target_h, :target_w]

    @property
    def is_loaded(self) -> bool:
        return self._loaded
