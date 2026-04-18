"""
Smart Bin configuration and environment variables.
"""

import os
from pydantic_settings import BaseSettings


class SmartBinSettings(BaseSettings):
    """Smart Bin application settings."""

    # Model paths
    model_path: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models", "waste.tflite")
    labels_path: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models", "labels.txt")

    # Camera
    camera_enabled: bool = True
    camera_mock: bool = False  # force mock mode for dev
    image_width: int = 224
    image_height: int = 224

    # Classification
    confidence_threshold: float = 0.5

    # Servo
    servo_return_delay: float = 3.0  # seconds before returning to base after sorting

    # Sensor (for /classify/auto)
    sensor_distance_cm: float = 15.0  # distance threshold to trigger classification

    # Dataset
    dataset_dir: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "dataset")
    images_dir: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "images")

    # Waste type → servo angle mapping (mirrors rpi_api config)
    waste_angles: dict = {
        "plastic": {"vertical": -90, "horizontal": -20},
        "glass": {"vertical": -90, "horizontal": 20},
        "pet": {"vertical": 90, "horizontal": -20},
        "organic": {"vertical": 90, "horizontal": 20},
        "other": {"vertical": 0, "horizontal": 0},
    }

    class Config:
        env_prefix = "SMART_BIN_"
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


smart_bin_settings = SmartBinSettings()
