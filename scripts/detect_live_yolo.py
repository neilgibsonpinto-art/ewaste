"""Fine-Tuned Live Webcam E-Waste Detection with Object Counter HUD.
Counts each sorted component (1 PCB, 2 PCBs, 1 Display, 2 Displays, etc.)
and displays real-time tally stats on screen.
"""

import cv2
import time
import urllib.request
from collections import deque
from pathlib import Path
from ultralytics import YOLO

# ================= CONFIGURATION =================
BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_PATH = BASE_DIR / "models" / "ewaste_yolov8n" / "weights" / "best.pt"

CAMERA_INDEX = 0
CONFIDENCE_THRESHOLD = 0.65  
MIN_BOX_AREA = 3500          
MAX_BOX_AREA = 180000        
REQUIRED_STABLE_FRAMES = 4   

# Conveyor Pick Zone (Center of screen)
ROI_RATIOS = (0.15, 0.20, 0.85, 0.85)

TRIGGER_ARM = True
ESP32_URL = "http://192.168.4.1/cmd?act=pick_and_place"
COOLDOWN_SECONDS = 7.0       

# Live Counts Dictionary
item_counts = {
    "pcb": 0,
    "battery": 0,
    "display": 0
}


def trigger_robotic_arm():
    if not TRIGGER_ARM:
        return False
    try:
        req = urllib.request.Request(ESP32_URL)
        with urllib.request.urlopen(req, timeout=2.0) as res:
            if res.status == 200:
                print("[ARM] Pick & Place executed successfully!")
                return True
    except Exception as e:
        print(f"[ARM NOTE] Wi-Fi link: {e}")
    return False


def is_inside_roi(box, frame_w, frame_h):
    x1, y1, x2, y2 = box
    cx = (x1 + x2) / 2.0
    cy = (y1 + y2) / 2.0
    rx1, ry1 = frame_w * ROI_RATIOS[0], frame_h * ROI_RATIOS[1]
    rx2, ry2 = frame_w * ROI_RATIOS[2], frame_h * ROI_RATIOS[3]
    return (rx1 <= cx <= rx2) and (ry1 <= cy <= ry2)


def draw_counter_hud(frame):
    """Draws a clean top HUD banner with real-time counts for each component."""
    h, w = frame.shape[:2]
    
    # Semi-transparent top bar
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, 50), (15, 23, 42), -1)
    cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)

    # Counts
    pcb_txt     = f"PCB: {item_counts['pcb']}"
    bat_txt     = f"BATTERY: {item_counts['battery']}"
    disp_txt    = f"DISPLAY: {item_counts['display']}"
    total_count = sum(item_counts.values())
    tot_txt     = f"TOTAL: {total_count}"

    cv2.putText(frame, pcb_txt, (20, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 128), 2)
    cv2.putText(frame, bat_txt, (160, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 215, 255), 2)
    cv2.putText(frame, disp_txt, (340, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 160, 50), 2)
    cv2.putText(frame, tot_txt, (520, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)


def main():
    print("=" * 60)
    print("  E-WASTE DETECTOR WITH REAL-TIME OBJECT COUNTER")
    print("=" * 60)
    print(f"[1/2] Loading model: {MODEL_PATH}")
    model = YOLO(str(MODEL_PATH))

    print(f"[2/2] Opening camera (Index {CAMERA_INDEX})...")
    cap = cv2.VideoCapture(CAMERA_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    if not cap.isOpened():
        print(f"[ERROR] Could not open camera {CAMERA_INDEX}.")
        return

    print("\n[READY] Point camera at e-waste inside the Pick Zone.")
    print("Controls: 'r' = Reset Counters | 'q' / 'ESC' = Quit\n")

    last_trigger_time = 0
    stable_tracker = deque(maxlen=REQUIRED_STABLE_FRAMES)

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            h, w = frame.shape[:2]
            now = time.time()
            in_cooldown = (now - last_trigger_time) < COOLDOWN_SECONDS

            # Draw Conveyor ROI Zone
            rx1, ry1 = int(w * ROI_RATIOS[0]), int(h * ROI_RATIOS[1])
            rx2, ry2 = int(w * ROI_RATIOS[2]), int(h * ROI_RATIOS[3])
            cv2.rectangle(frame, (rx1, ry1), (rx2, ry2), (255, 255, 0), 2)
            cv2.putText(frame, "CONVEYOR PICK ZONE", (rx1 + 5, ry1 - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)

            # Run YOLOv8 inference
            results = model(frame, conf=CONFIDENCE_THRESHOLD, verbose=False)

            verified_detections = []
            for r in results:
                for box in r.boxes:
                    cls_id = int(box.cls[0])
                    cls_name = model.names[cls_id]
                    conf = float(box.conf[0])
                    x1, y1, x2, y2 = map(int, box.xyxy[0])

                    box_area = (x2 - x1) * (y2 - y1)
                    if box_area < MIN_BOX_AREA or box_area > MAX_BOX_AREA:
                        continue

                    if not is_inside_roi((x1, y1, x2, y2), w, h):
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (80, 80, 80), 1)
                        continue

                    color = (0, 255, 0) if not in_cooldown else (0, 165, 255)
                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                    label_text = f"{cls_name.upper()} {conf:.2f}"
                    cv2.putText(frame, label_text, (x1, max(65, y1 - 8)),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                    verified_detections.append(cls_name)

            # Temporal Stability Filter
            if verified_detections:
                stable_tracker.append(verified_detections[0])
            else:
                stable_tracker.clear()

            is_stable = (len(stable_tracker) == REQUIRED_STABLE_FRAMES and 
                         len(set(stable_tracker)) == 1)

            # Status Message at bottom
            if in_cooldown:
                status_text = "ARM BUSY (SORTING...)"
                status_color = (0, 165, 255)
            elif is_stable:
                status_text = f"CONFIRMED: {stable_tracker[0].upper()}"
                status_color = (0, 255, 0)
            else:
                status_text = "SCANNING CONVEYOR..."
                status_color = (200, 200, 200)

            cv2.putText(frame, f"STATUS: {status_text}", (20, h - 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.65, status_color, 2)

            # COUNT & TRIGGER when object is confirmed stable
            if is_stable and not in_cooldown:
                confirmed_item = stable_tracker[0]
                if confirmed_item in item_counts:
                    item_counts[confirmed_item] += 1
                    current_count = item_counts[confirmed_item]
                    print(f"\n[COUNT UPDATE] -> {confirmed_item.upper()} #{current_count} (Total: {sum(item_counts.values())})")

                trigger_robotic_arm()
                last_trigger_time = time.time()
                stable_tracker.clear()

            # Render Live Top HUD Bar
            draw_counter_hud(frame)

            cv2.imshow("E-Waste Sorter & Counter", frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('r') or key == ord('R'):
                item_counts["pcb"] = 0
                item_counts["battery"] = 0
                item_counts["display"] = 0
                print("\n[INFO] All counts reset to 0.")
            elif key == ord('q') or key == 27:
                break

    finally:
        cap.release()
        cv2.destroyAllWindows()
        print("\n=== FINAL SORTING TALLY ===")
        print(f"  PCBs Sorted      : {item_counts['pcb']}")
        print(f"  Batteries Sorted : {item_counts['battery']}")
        print(f"  Displays Sorted  : {item_counts['display']}")
        print(f"  Total Processed  : {sum(item_counts.values())}")
        print("===========================")


if __name__ == "__main__":
    main()
