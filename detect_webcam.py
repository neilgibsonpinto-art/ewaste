"""Live E-Waste detection using normal laptop webcam or USB webcam (OpenCV)."""

import cv2
import time
import requests
import numpy as np
from PIL import Image
from pathlib import Path
import sys

# Add referenced path if needed
detector_dir = Path(r"C:\Users\Neil Gibson Pinto\Documents\Codex\2026-11-10\referenced-chatgpt-conversation-this-is-an-3\outputs\laptop-d435")
if str(detector_dir) not in sys.path:
    sys.path.append(str(detector_dir))

from detect import Detector

# ================= CONFIGURATION =================
CAMERA_INDEX = 0             # 0 = Built-in laptop webcam, 1 = External USB webcam
DETECTION_THRESHOLD = 0.58   # Match sensitivity (0.50 to 0.70)
TRIGGER_ARM = True           # Set to True to send commands to ESP32, False for view only
ESP32_URL = "http://192.168.4.1/cmd?act=pick_and_place"
COOLDOWN_SECONDS = 7.0       # Delay to allow robotic arm to finish pick & drop cycle


def send_arm_trigger():
    if not TRIGGER_ARM:
        return False
    try:
        print("[ARM] Triggering Pick & Place on ESP32...")
        res = requests.get(ESP32_URL, timeout=2.0)
        if res.status_code == 200:
            print("[ARM SUCCESS] Sorter sequence initiated on robotic arm!")
            return True
    except Exception as e:
        print(f"[ARM NOTE] Arm not reachable (Wi-Fi disconnected): {e}")
    return False


def main():
    print("=" * 60)
    print("  LIVE WEBCAM E-WASTE DETECTOR (NORMAL LAPTOP / USB CAM)")
    print("=" * 60)

    print("[1/2] Loading reference templates...")
    detector = Detector()

    print(f"[2/2] Opening camera (Index {CAMERA_INDEX})...")
    cap = cv2.VideoCapture(CAMERA_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    if not cap.isOpened():
        print(f"[ERROR] Could not open camera {CAMERA_INDEX}.")
        print("Try changing CAMERA_INDEX = 1 if using an external USB webcam.")
        return

    print("\n[READY] Camera live! Point your laptop webcam at your e-waste.")
    print("Controls: Press 'q' or 'ESC' on the video window to quit.\n")

    last_trigger_time = 0

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("[WARN] Failed to grab frame.")
                break

            now = time.time()
            in_cooldown = (now - last_trigger_time) < COOLDOWN_SECONDS

            # Convert BGR frame to RGB PIL image for detector
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(rgb_frame)

            # Run template matching
            hits = detector.detect(pil_image, threshold=DETECTION_THRESHOLD)

            # Draw visual feedback
            status_text = "ARM BUSY (SORTING...)" if in_cooldown else "SCANNING..."
            status_color = (0, 165, 255) if in_cooldown else (0, 255, 0)
            cv2.putText(frame, f"STATUS: {status_text}", (20, 35),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.75, status_color, 2)

            for score, label, (x1, y1, x2, y2) in hits:
                color = (0, 255, 0) if not in_cooldown else (0, 165, 255)
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                caption = f"{label} | match {score:.2f}"
                cv2.putText(frame, caption, (x1, max(20, y1 - 8)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)

            # Trigger arm if object detected and arm is ready
            if hits and not in_cooldown:
                top_score, top_label, _ = hits[0]
                print(f"[DETECTED] {top_label} (Match: {top_score:.2f}) -> Triggering Arm!")
                send_arm_trigger()
                last_trigger_time = time.time()

            # Show window
            cv2.imshow("Laptop Webcam E-Waste Detection", frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == 27:
                break

    finally:
        cap.release()
        cv2.destroyAllWindows()
        print("[INFO] Camera released. Exited cleanly.")


if __name__ == "__main__":
    main()
