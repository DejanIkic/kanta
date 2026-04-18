"""
RPi5 camera module using picamera2.
Falls back to mock if camera unavailable or picamera2 not installed.
"""

import os
import logging
from typing import Optional

import numpy as np

from ..config import smart_bin_settings

logger = logging.getLogger(__name__)

# Try importing picamera2
_picamera2_available = False
_Picamera2 = None

try:
    from picamera2 import Picamera2
    _picamera2_available = True
    _Picamera2 = Picamera2
except ImportError:
    logger.info("picamera2 not available - using mock camera")

_camera_instance: Optional[_Picamera2] = None


def get_camera() -> Optional[object]:
    """
    Get or create picamera2 instance.
    Returns None if camera unavailable.
    """
    global _camera_instance

    if not _picamera2_available or smart_bin_settings.camera_mock:
        return None

    if _camera_instance is None:
        try:
            _camera_instance = _Picamera2()
            # Configure for still capture
            config = _camera_instance.create_still_configuration(
                main={"size": (
                    smart_bin_settings.image_width,
                    smart_bin_settings.image_height,
                )}
            )
            _camera_instance.configure(config)
            _camera_instance.start()
            logger.info("picamera2 initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize picamera2: {e}")
            _camera_instance = None

    return _camera_instance


def take_photo() -> np.ndarray:
    """
    Capture a photo from picamera2.
    Returns mock image if camera unavailable.

    :return: Image as numpy array (H, W, C), uint8.
    """
    cam = get_camera()

    if cam is not None:
        try:
            # Capture array directly
            img = cam.capture_array("main")
            # picamera2 returns RGB, convert to BGR for consistency with cv2
            if img.ndim == 3 and img.shape[2] == 3:
                img = img[:, :, ::-1]
            return img.astype(np.uint8)
        except Exception as e:
            logger.warning(f"Camera capture failed: {e}, using mock")

    # Mock: return noise image
    return _mock_image()


def _mock_image() -> np.ndarray:
    """Generate a mock image for development without camera."""
    h = smart_bin_settings.image_height
    w = smart_bin_settings.image_width
    # Random noise image (BGR)
    rng = np.random.default_rng()
    img = rng.integers(0, 256, (h, w, 3), dtype=np.uint8)
    return img


def cleanup_camera() -> None:
    """Stop and release camera resources."""
    global _camera_instance
    if _camera_instance is not None:
        try:
            _camera_instance.stop()
        except Exception:
            pass
        _camera_instance = None
