"""Camera abstraction layer."""

from .pi_camera import take_photo, get_camera, cleanup_camera

__all__ = ["take_photo", "get_camera", "cleanup_camera"]
