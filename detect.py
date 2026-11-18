"""E-Waste Real-Time Detection and Sorting Counter.
Runs directly from root folder on laptop webcam or external USB camera.
"""
import sys
from pathlib import Path

# Redirect directly to scripts/detect_live_yolo.py
from scripts.detect_live_yolo import main

if __name__ == "__main__":
    main()
