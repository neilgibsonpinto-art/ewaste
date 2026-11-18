"""Prepares and auto-annotates the extracted 92 e-waste images into YOLOv8 format."""

import os
import sys
import shutil
import random
import cv2
import numpy as np
from PIL import Image
from pathlib import Path

# Paths
BASE_DIR = Path(r"c:\Users\Neil Gibson Pinto\Documents\antigravity\magical-volta")
RAW_DIR = BASE_DIR / "dataset" / "raw"
DATASET_DIR = BASE_DIR / "dataset"

# Reference detector from existing project
DETECTOR_DIR = Path(r"C:\Users\Neil Gibson Pinto\Documents\Codex\2026-11-10\referenced-chatgpt-conversation-this-is-an-3\outputs\laptop-d435")
if str(DETECTOR_DIR) not in sys.path:
    sys.path.append(str(DETECTOR_DIR))

from detect import Detector

CLASS_MAP = {
    "Red circuit board": 0,    # pcb
    "Cylindrical battery": 1,  # battery
    "Seven-segment display": 2 # display
}


def fallback_bounding_box(image_path, img_w, img_h, page_num):
    """Fallback segmenter using background subtraction if template misses."""
    img = cv2.imread(str(image_path))
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Invert threshold since scanner background is light/white
    _, thresh = cv2.threshold(blurred, 220, 255, cv2.THRESH_BINARY_INV)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Assign class based on known DocScanner page partitions if ambiguous
    if 1 <= page_num <= 32 or 71 <= page_num <= 85:
        cls_id = 0 # pcb
    elif 33 <= page_num <= 52 or 86 <= page_num <= 92:
        cls_id = 1 # battery
    else:
        cls_id = 2 # display

    boxes = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area > (img_w * img_h * 0.03): # At least 3% of page area
            x, y, w, h = cv2.boundingRect(cnt)
            # Normalize to YOLO format
            xc = (x + w / 2.0) / img_w
            yc = (y + h / 2.0) / img_h
            nw = w / float(img_w)
            nh = h / float(img_h)
            boxes.append((cls_id, xc, yc, nw, nh))
            break # Take dominant object
            
    if not boxes:
        # Default centered bounding box covering main object
        boxes.append((cls_id, 0.5, 0.5, 0.65, 0.65))
    return boxes


def main():
    print("[1/4] Initializing Template Detector...")
    detector = Detector()

    # Create target YOLO directory structure
    for split in ["train", "val"]:
        (DATASET_DIR / "images" / split).mkdir(parents=True, exist_ok=True)
        (DATASET_DIR / "labels" / split).mkdir(parents=True, exist_ok=True)

    raw_images = sorted(list(RAW_DIR.glob("sample_*.jpeg")) + list(RAW_DIR.glob("sample_*.jpg")))
    print(f"[2/4] Found {len(raw_images)} raw images. Auto-annotating...")

    # Set random seed for reproducible 80/20 train/val split
    random.seed(42)
    random.shuffle(raw_images)
    split_idx = int(len(raw_images) * 0.80)
    train_files = set(raw_images[:split_idx])

    annotated_count = 0
    for idx, img_path in enumerate(raw_images):
        page_num = int(img_path.stem.split("_")[-1])
        split = "train" if img_path in train_files else "val"
        
        with Image.open(img_path) as im:
            w, h = im.size
            hits = detector.detect(im, threshold=0.48)

        yolo_boxes = []
        if hits:
            for score, label, (x1, y1, x2, y2) in hits:
                cls_id = CLASS_MAP.get(label, 0)
                xc = ((x1 + x2) / 2.0) / w
                yc = ((y1 + y2) / 2.0) / h
                nw = (x2 - x1) / float(w)
                nh = (y2 - y1) / float(h)
                yolo_boxes.append((cls_id, xc, yc, nw, nh))
        else:
            yolo_boxes = fallback_bounding_box(img_path, w, h, page_num)

        # Copy image to destination
        dest_img = DATASET_DIR / "images" / split / f"ewaste_{page_num:03d}.jpg"
        shutil.copy(img_path, dest_img)

        # Write YOLO label .txt file
        dest_lbl = DATASET_DIR / "labels" / split / f"ewaste_{page_num:03d}.txt"
        with open(dest_lbl, "w") as f:
            for cls_id, xc, yc, nw, nh in yolo_boxes:
                f.write(f"{cls_id} {xc:.6f} {yc:.6f} {nw:.6f} {nh:.6f}\n")

        annotated_count += 1
        if (idx + 1) % 20 == 0 or idx == len(raw_images) - 1:
            print(f"Processed {idx + 1}/{len(raw_images)} images...")

    # Write data.yaml
    data_yaml_content = f"""path: {DATASET_DIR.as_posix()}
train: images/train
val: images/val

names:
  0: pcb
  1: battery
  2: display
"""
    with open(DATASET_DIR / "data.yaml", "w") as f:
        f.write(data_yaml_content)

    print(f"\n[3/4] Dataset formatting completed!")
    print(f"  - Total images: {annotated_count}")
    print(f"  - Train split : {split_idx} images")
    print(f"  - Val split   : {len(raw_images) - split_idx} images")
    print(f"  - YAML config : {DATASET_DIR / 'data.yaml'}")


if __name__ == "__main__":
    main()
