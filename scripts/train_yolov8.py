"""Trains a lightweight YOLOv8-Nano model on the annotated E-Waste dataset."""

import os
import torch
from pathlib import Path
from ultralytics import YOLO

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_YAML = BASE_DIR / "dataset" / "data.yaml"
LOCAL_WEIGHTS = BASE_DIR / "yolov8n.pt"


def main():
    print("=" * 60)
    print("  TRAINING LIGHTWEIGHT YOLOv8-NANO ON E-WASTE DATASET")
    print("=" * 60)

    device = "0" if torch.cuda.is_available() else "cpu"
    print(f"[DEVICE] Training on: {device.upper()}")
    print(f"[MODEL] Loading local weights: {LOCAL_WEIGHTS}")

    # Load local YOLOv8-nano weights
    model = YOLO(str(LOCAL_WEIGHTS))

    # Start training (25 epochs)
    results = model.train(
        data=str(DATA_YAML),
        epochs=25,
        imgsz=640,
        batch=8,
        name="ewaste_yolov8n",
        project=str(BASE_DIR / "models"),
        device=device,
        plots=True,
        verbose=True
    )

    best_pt = BASE_DIR / "models" / "ewaste_yolov8n" / "weights" / "best.pt"
    print("\n" + "=" * 60)
    print("  TRAINING COMPLETE!")
    print(f"  Best Weights Saved: {best_pt}")
    print("=" * 60)

    # Export to ONNX format
    try:
        print("\n[EXPORT] Exporting model to ONNX format...")
        model.export(format="onnx", imgsz=640)
        print("[EXPORT] Successfully exported to ONNX format!")
    except Exception as e:
        print(f"[EXPORT NOTE] ONNX export skipped: {e}")


if __name__ == "__main__":
    main()
