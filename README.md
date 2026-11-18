# Smart E-Waste Segregation System (Robotic Arm + YOLOv8 Vision)

An automated conveyor-based electronic waste (e-waste) segregation system. It detects and classifies electronic waste into distinct categories (**PCBs**, **Batteries**, and **Displays**) using a custom-trained **YOLOv8-Nano** model and actuates a **6-DOF robotic arm** via **ESP32** over Wi-Fi to sort items into designated bins.

---

## System Architecture

```mermaid
flowchart LR
    A[Conveyor Belt with E-Waste] --> B[Camera / Webcam Feed]
    B --> C[YOLOv8 Detection & Counting Engine]
    C -->|HTTP REST over Wi-Fi| D[ESP32 Motion Controller]
    D --> E[6-DOF Robotic Arm]
    E --> F[Segregation Bins: Battery | PCB | Display]
```

---

## Features
* **Custom YOLOv8-Nano Detection:** Trained directly on physical scanned e-waste components (`pcb`, `battery`, `display`).
* **Real-time Noise Filtering:** Temporal debouncing and a designated conveyor Region of Interest (ROI) prevent false triggers.
* **On-Screen Object Counter HUD:** Tracks and displays individual tallies for each component in real time.
* **ESP32 6-DOF Robotic Arm:** Smooth non-blocking trajectory easing to eliminate mechanical jerk on high-torque 20kg servos.
* **Standalone Wi-Fi Hotspot:** No external router needed; the ESP32 hosts its own AP at `http://192.168.4.1`.

---

## Hardware Specifications
* **Host Compute:** Laptop / Raspberry Pi 5
* **Camera:** USB Webcam / Intel RealSense D435
* **Microcontroller:** ESP32 Dev Board (Direct PWM)
* **Actuators:**
  * Base & Shoulder: TianKongRC TD-8120MG 20KG High-Torque Servos
  * Elbow, Wrist & Gripper: Metal gear digital servos
* **Power:** 12V Battery with DC-DC Buck Converter (5V/6V shared ground)

---

## Calibrated Servo Positions
* **Home Resting Stance:** `[90°, 75°, 115°, 60°, 90°, 45°]`
* **Conveyor Pick Pose:** `[99°, 84°, 124°, 80°, 122°, 131°]` (Claw Grip: 131°, Open: 30°)
* **Bin Place Pose:** `[0°, 110°, 124°, 80°, 122°, 30°]` (Base 0°, Release: 30°)

---

## Quickstart

### 1. Installation
```bash
python -m venv ewaste_env
# Windows:
.\ewaste_env\Scripts\activate
# Linux/Mac:
source ewaste_env/bin/activate

pip install -r requirements.txt
```

### 2. Run Live Detection & Counter
```bash
python scripts/detect_live_yolo.py
```

### 3. Flash Robotic Arm Firmware
Open `esp32/SorterArm/SorterArm.ino` in Arduino IDE, select your ESP32 board, and click Upload.
