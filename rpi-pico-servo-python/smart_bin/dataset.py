"""
Dataset collection utilities for Smart Bin.
Handles image saving, CSV logging, and light level estimation.
"""

import base64
import csv
import os
from datetime import datetime, timezone
from typing import Optional

import numpy as np

from .config import smart_bin_settings

CSV_HEADER = "img_path,predicted_class,user_label,confidence,timestamp,angle,light_level"


def estimate_light_level(image: np.ndarray) -> float:
    """
    Estimate light level from image brightness.
    Mean pixel value normalized to [0, 1].

    :param image: BGR image as numpy array.
    :return: Light level between 0.0 (dark) and 1.0 (bright).
    """
    if image.size == 0:
        return 0.0
    # Convert BGR to grayscale luminance approximation
    gray = np.mean(image, axis=(0, 1))
    # Weighted luminance: B*0.114 + G*0.587 + R*0.299
    luminance = gray[0] * 0.114 + gray[1] * 0.587 + gray[2] * 0.299
    return round(luminance / 255.0, 4)


def save_image(image: np.ndarray, directory: str, prefix: str = "img") -> str:
    """
    Save image to disk as JPEG.

    :param image: BGR image as numpy array.
    :param directory: Target directory.
    :param prefix: Filename prefix.
    :return: Saved file path.
    """
    os.makedirs(directory, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
    filename = f"{prefix}_{timestamp}.jpg"
    filepath = os.path.join(directory, filename)

    try:
        import cv2
        cv2.imwrite(filepath, image)
    except ImportError:
        # Fallback: save as raw numpy if cv2 unavailable
        np.save(filepath.replace(".jpg", ".npy"), image)
        filepath = filepath.replace(".jpg", ".npy")

    return filepath


def decode_b64_image(image_b64: str) -> np.ndarray:
    """
    Decode base64-encoded JPEG to numpy array.

    :param image_b64: Base64-encoded image string.
    :return: BGR image as numpy array.
    """
    img_bytes = base64.b64decode(image_b64)

    try:
        import cv2
        img_array = np.frombuffer(img_bytes, dtype=np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
    except ImportError:
        # Fallback: cannot decode JPEG without cv2
        raise ImportError("cv2 required for image decoding. Install opencv-python-headless.")

    if img is None:
        raise ValueError("Failed to decode base64 image")

    return img


def append_to_labels_csv(
    img_path: str,
    predicted_class: str,
    confidence: float,
    angle: int,
    light_level: float,
    user_label: str = "",
) -> int:
    """
    Append a row to labels.csv.

    :return: Row ID (line number in CSV, 0-indexed after header).
    """
    csv_path = os.path.join(smart_bin_settings.dataset_dir, "labels.csv")
    os.makedirs(smart_bin_settings.dataset_dir, exist_ok=True)

    # Create CSV with header if not exists
    if not os.path.exists(csv_path):
        with open(csv_path, "w", newline="") as f:
            f.write(CSV_HEADER + "\n")

    timestamp = datetime.now(timezone.utc).isoformat()

    with open(csv_path, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([img_path, predicted_class, user_label, confidence, timestamp, angle, light_level])

    # Count rows to get row_id
    with open(csv_path, "r") as f:
        reader = csv.reader(f)
        row_count = sum(1 for _ in reader) - 1  # exclude header

    return row_count


def read_labels_csv() -> list[dict]:
    """
    Read all entries from labels.csv.

    :return: List of dicts with label data.
    """
    csv_path = os.path.join(smart_bin_settings.dataset_dir, "labels.csv")

    if not os.path.exists(csv_path):
        return []

    entries = []
    with open(csv_path, "r") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            entry = dict(row)
            entry["row_id"] = i
            entries.append(entry)

    return entries


def update_user_label(row_id: int, user_label: str) -> bool:
    """
    Update user_label field for a specific row in labels.csv.

    :param row_id: Row index (0-based, after header).
    :param user_label: New ground truth label.
    :return: True if updated, False if row not found.
    """
    csv_path = os.path.join(smart_bin_settings.dataset_dir, "labels.csv")

    if not os.path.exists(csv_path):
        return False

    rows = []
    with open(csv_path, "r") as f:
        reader = csv.reader(f)
        header = next(reader)
        rows = list(reader)

    if row_id < 0 or row_id >= len(rows):
        return False

    # user_label is column index 2
    rows[row_id][2] = user_label

    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)

    return True


def save_to_dataset(
    image: np.ndarray,
    predicted_class: str,
    confidence: float,
    angle: int,
) -> tuple[str, int, float]:
    """
    Save image to dataset and log in labels.csv.

    :param image: BGR image as numpy array.
    :param predicted_class: Predicted waste type.
    :param confidence: Classification confidence.
    :param angle: Servo angle used.
    :return: Tuple of (image_path, row_id, light_level).
    """
    images_dir = os.path.join(smart_bin_settings.dataset_dir, "images")
    img_path = save_image(image, images_dir, prefix="capture")
    light_level = estimate_light_level(image)
    row_id = append_to_labels_csv(
        img_path=img_path,
        predicted_class=predicted_class,
        confidence=confidence,
        angle=angle,
        light_level=light_level,
    )
    return img_path, row_id, light_level
