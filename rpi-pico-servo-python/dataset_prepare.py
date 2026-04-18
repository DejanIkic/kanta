"""
Dataset preparation script for Smart Bin.
- Reads labels.csv
- Splits into train/val/test (70/20/10)
- Augments images (flip, rotate, brightness)
- Balances classes by oversampling minority
"""

import csv
import os
import random
import shutil
from collections import defaultdict
from pathlib import Path

import numpy as np

DATASET_DIR = os.path.join(os.path.dirname(__file__), "dataset")
LABELS_CSV = os.path.join(DATASET_DIR, "labels.csv")
OUTPUT_DIR = os.path.join(DATASET_DIR, "prepared")

SPLIT_RATIOS = {"train": 0.7, "val": 0.2, "test": 0.1}

# Augmentation settings
AUGMENTATIONS_PER_IMAGE = 3


def read_labels():
    """Read labels.csv and return list of dicts."""
    if not os.path.exists(LABELS_CSV):
        print(f"ERROR: {LABELS_CSV} not found")
        return []

    entries = []
    with open(LABELS_CSV, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            entries.append(dict(row))
    return entries


def split_dataset(entries):
    """Split entries into train/val/test by class proportion."""
    by_class = defaultdict(list)
    for e in entries:
        by_class[e["predicted_class"]].append(e)

    splits = {"train": [], "val": [], "test": []}

    for cls, items in by_class.items():
        random.shuffle(items)
        n = len(items)
        n_train = max(1, int(n * SPLIT_RATIOS["train"]))
        n_val = max(1, int(n * SPLIT_RATIOS["val"]))
        n_test = max(0, n - n_train - n_val)

        splits["train"].extend(items[:n_train])
        splits["val"].extend(items[n_train:n_train + n_val])
        splits["test"].extend(items[n_train + n_val:])

    return splits


def copy_images(splits):
    """Copy images to train/val/test directories."""
    for split_name, entries in splits.items():
        split_dir = os.path.join(OUTPUT_DIR, split_name)
        os.makedirs(split_dir, exist_ok=True)

        for entry in entries:
            src = entry["img_path"]
            if not os.path.exists(src):
                print(f"WARNING: Image not found: {src}")
                continue

            dst = os.path.join(split_dir, os.path.basename(src))
            shutil.copy2(src, dst)

        # Write split CSV
        csv_path = os.path.join(OUTPUT_DIR, f"{split_name}.csv")
        with open(csv_path, "w", newline="") as f:
            if entries:
                writer = csv.DictWriter(f, fieldnames=entries[0].keys())
                writer.writeheader()
                writer.writerows(entries)

        print(f"  {split_name}: {len(entries)} images -> {split_dir}")


def augment_images(splits):
    """
    Augment images to balance classes.
    Uses cv2 if available, else numpy-only augmentations.
    """
    try:
        import cv2
        has_cv2 = True
    except ImportError:
        has_cv2 = False
        print("cv2 not available - using numpy-only augmentations (flip only)")

    # Count per class in training set
    train = splits["train"]
    by_class = defaultdict(list)
    for e in train:
        by_class[e["predicted_class"]].append(e)

    if not by_class:
        return splits

    max_count = max(len(v) for v in by_class.values())
    train_dir = os.path.join(OUTPUT_DIR, "train")

    augmented = []
    for cls, items in by_class.items():
        deficit = max_count - len(items)
        if deficit <= 0:
            continue

        print(f"  Augmenting '{cls}': {len(items)} -> {max_count} (+{deficit})")

        for i in range(deficit):
            source = items[i % len(items)]
            src_path = source["img_path"]

            if not os.path.exists(src_path):
                continue

            # Load image
            if has_cv2:
                img = cv2.imread(src_path)
                if img is None:
                    continue
                img = _augment_cv2(img, i)
            else:
                img = np.load(src_path.replace(".jpg", ".npy")) if src_path.endswith(".npy") else None
                if img is None:
                    continue
                img = _augment_numpy(img, i)

            # Save augmented
            aug_name = f"aug_{i}_{os.path.basename(src_path)}"
            aug_path = os.path.join(train_dir, aug_name)

            if has_cv2:
                import cv2
                cv2.imwrite(aug_path, img)
            else:
                np.save(aug_path.replace(".jpg", ".npy"), img)
                aug_path = aug_path.replace(".jpg", ".npy")

            aug_entry = dict(source)
            aug_entry["img_path"] = aug_path
            augmented.append(aug_entry)

    splits["train"].extend(augmented)
    return splits


def _augment_cv2(img, seed):
    """Apply random augmentation using cv2."""
    import cv2

    rng = random.Random(seed)
    choice = rng.randint(0, 3)

    if choice == 0:
        # Horizontal flip
        img = cv2.flip(img, 1)
    elif choice == 1:
        # Vertical flip
        img = cv2.flip(img, 0)
    elif choice == 2:
        # Rotate small angle
        angle = rng.uniform(-15, 15)
        h, w = img.shape[:2]
        M = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
        img = cv2.warpAffine(img, M, (w, h))
    else:
        # Brightness jitter
        factor = rng.uniform(0.7, 1.3)
        img = np.clip(img.astype(np.float32) * factor, 0, 255).astype(np.uint8)

    return img


def _augment_numpy(img, seed):
    """Apply basic augmentation using numpy only (flip)."""
    rng = random.Random(seed)
    if rng.random() > 0.5:
        img = np.fliplr(img).copy()
    return img


def main():
    print("=" * 50)
    print("Smart Bin Dataset Preparation")
    print("=" * 50)

    entries = read_labels()
    if not entries:
        print("No entries found. Run /capture endpoint first.")
        return

    print(f"\nTotal entries: {len(entries)}")

    # Class distribution
    by_class = defaultdict(int)
    for e in entries:
        by_class[e["predicted_class"]] += 1
    print("Class distribution:")
    for cls, count in sorted(by_class.items()):
        print(f"  {cls}: {count}")

    # Split
    print("\nSplitting dataset...")
    splits = split_dataset(entries)

    # Prepare output
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Copy images
    print("\nCopying images...")
    copy_images(splits)

    # Augment training set
    print("\nAugmenting training set...")
    splits = augment_images(splits)

    # Update train CSV with augmented entries
    train_csv = os.path.join(OUTPUT_DIR, "train.csv")
    if splits["train"]:
        with open(train_csv, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=splits["train"][0].keys())
            writer.writeheader()
            writer.writerows(splits["train"])

    print(f"\nDone! Prepared dataset at: {OUTPUT_DIR}")
    print(f"  train: {len(splits['train'])}")
    print(f"  val:   {len(splits['val'])}")
    print(f"  test:  {len(splits['test'])}")


if __name__ == "__main__":
    main()
