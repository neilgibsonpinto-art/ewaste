#include <WiFi.h>
#include <WebServer.h>
#include <ESP32Servo.h>

// ================= 1. HOTSPOT NETWORK CONFIG =================
const char* AP_SSID = "RoboArm-Hotspot";
const char* AP_PASS = "12345678"; // Minimum 8 characters

IPAddress local_IP(192, 168, 4, 1);
IPAddress gateway(192, 168, 4, 1);
IPAddress subnet(255, 255, 255, 0);

// ================= 2. PIN ASSIGNMENTS ========================
#define NUM_SERVOS 6
const int SERVO_PINS[NUM_SERVOS] = {
  13, // Joint 0: Base Waist (TD-8120MG 20KG)
  12, // Joint 1: Shoulder (TD-8120MG 20KG)
  4,  // Joint 2: Elbow
  27, // Joint 3: Wrist Pitch
  26, // Joint 4: Wrist Roll
  25  // Joint 5: Gripper Claw
};

Servo servos[NUM_SERVOS];

// ================= 3. CALIBRATED HOME ANGLES (FROM PHOTO) ====
// Matches the downward ready-to-pick posture of your robotic arm:
const float HOME_ANGLES[NUM_SERVOS] = {
  90.0,  // Base: Centered straight forward
  75.0,  // Shoulder: Leaning forward
  115.0, // Elbow: Folded downward
  60.0,  // Wrist Pitch: Pointing claw toward the sorting area
  90.0,  // Wrist Roll: Centered
  45.0   // Gripper: Relaxed / Open
};

// Current positions and target positions
float currentPos[NUM_SERVOS];
float targetPos[NUM_SERVOS];

// Maximum degrees per 15ms step (Tuned for 20kg high-torque servos + long arm linkage)
const float STEP_SPEED[NUM_SERVOS] = {
  0.7, // Base (Moderate inertia)
  0.5, // Shoulder (Carries entire arm weight + battery leverage - gentlest)
  0.6, // Elbow (Smooth downward motion)
  0.9, // Wrist Pitch
  1.1, // Wrist Roll
  1.5  // Gripper
};

const unsigned long UPDATE_INTERVAL_MS = 15;
unsigned long lastUpdate = 0;

WebServer server(80);

// ================= 4. RESPONSIVE WEB UI (PROGMEM) ============
const char HTML_PAGE[] PROGMEM = R"rawliteral(
<!DOCTYPE html>
<html>
<head>
  <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
  <title>Smart E-Waste Arm Controller</title>
  <style>
    * { box-sizing: border-box; font-family: system-ui, -apple-system, sans-serif; -webkit-tap-highlight-color: transparent; }
    body { background-color: #0b0f19; color: #f1f5f9; margin: 0; padding: 14px; display: flex; justify-content: center; }
    .card { background: #151d30; width: 100%; max-width: 440px; padding: 22px; border-radius: 18px; box-shadow: 0 12px 32px rgba(0,0,0,0.5); }
    .badge { display: inline-block; background: #22c55e; color: #000; font-size: 11px; font-weight: 800; padding: 3px 9px; border-radius: 20px; text-transform: uppercase; margin-bottom: 8px; }
    h2 { margin: 4px 0 16px 0; color: #38bdf8; font-size: 21px; }
    .slider-box { margin-bottom: 16px; }
    .slider-label { display: flex; justify-content: space-between; font-size: 13px; font-weight: 600; margin-bottom: 6px; color: #94a3b8; }
    .val { color: #38bdf8; font-size: 14px; font-weight: 700; }
    input[type=range] { width: 100%; height: 8px; border-radius: 4px; background: #263352; outline: none; -webkit-appearance: none; }
    input[type=range]::-webkit-slider-thumb { -webkit-appearance: none; width: 24px; height: 24px; border-radius: 50%; background: #38bdf8; cursor: pointer; box-shadow: 0 0 10px rgba(56,189,248,0.5); }
    .btn-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 22px; }
    button { background: #1e293b; border: 1px solid #334155; color: #fff; padding: 12px; font-size: 13px; font-weight: 700; border-radius: 10px; cursor: pointer; transition: 0.15s; }
    button:active { background: #38bdf8; color: #000; }
    .btn-home { grid-column: span 2; background: #38bdf8; color: #0b0f19; font-size: 14px; border: none; }
  </style>
</head>
<body>
  <div class="card">
    <span class="badge">Hotspot Connected</span>
    <h2>6-DOF ROBOTIC ARM</h2>

    <div class="slider-box">
      <div class="slider-label"><span>Base (GPIO 13)</span><span class="val" id="v0">90°</span></div>
      <input type="range" id="s0" min="0" max="180" value="90" oninput="queueUpdate(0, this.value)">
    </div>

    <div class="slider-box">
      <div class="slider-label"><span>Shoulder (GPIO 12)</span><span class="val" id="v1">75°</span></div>
      <input type="range" id="s1" min="0" max="180" value="75" oninput="queueUpdate(1, this.value)">
    </div>

    <div class="slider-box">
      <div class="slider-label"><span>Elbow (GPIO 4)</span><span class="val" id="v2">115°</span></div>
      <input type="range" id="s2" min="0" max="180" value="115" oninput="queueUpdate(2, this.value)">
    </div>

    <div class="slider-box">
      <div class="slider-label"><span>Wrist Pitch (GPIO 27)</span><span class="val" id="v3">60°</span></div>
      <input type="range" id="s3" min="0" max="180" value="60" oninput="queueUpdate(3, this.value)">
    </div>

    <div class="slider-box">
      <div class="slider-label"><span>Wrist Roll (GPIO 26)</span><span class="val" id="v4">90°</span></div>
      <input type="range" id="s4" min="0" max="180" value="90" oninput="queueUpdate(4, this.value)">
    </div>

    <div class="slider-box">
      <div class="slider-label"><span>Gripper Claw (GPIO 25)</span><span class="val" id="v5">45°</span></div>
      <input type="range" id="s5" min="0" max="180" value="45" oninput="queueUpdate(5, this.value)">
    </div>

    <div class="btn-grid">
      <button class="btn-home" onclick="triggerPreset('home')">Smooth Home Pose</button>
      <button onclick="triggerPreset('open')">Open Claw</button>
      <button onclick="triggerPreset('close')">Close Claw</button>
    </div>
  </div>

  <script>
    let pending = {};
    let timer = null;

    function queueUpdate(id, val) {
      document.getElementById('v' + id).innerText = val + '°';
      pending[id] = val;
      if (!timer) {
        timer = setTimeout(() => {
          for (let k in pending) {
            fetch('/set?id=' + k + '&val=' + pending[k]);
          }
          pending = {};
          timer = null;
        }, 50);
      }
    }

    function triggerPreset(act) {
      fetch('/cmd?act=' + act);
      if (act === 'home') {
        const homeVals = [90, 75, 115, 60, 90, 45];
        homeVals.forEach((val, i) => {
          document.getElementById('s' + i).value = val;
          document.getElementById('v' + i).innerText = val + '°';
        });
      } else if (act === 'open') {
        document.getElementById('s5').value = 30;
        document.getElementById('v5').innerText = '30°';
      } else if (act === 'close') {
        document.getElementById('s5').value = 120;
        document.getElementById('v5').innerText = '120°';
      }
    }
  </script>
</body>
</html>
)rawliteral";

// ================= 5. WEB SERVER HANDLERS ====================
void handleRoot() {
  server.send(200, "text/html", HTML_PAGE);
}

void handleSet() {
  if (server.hasArg("id") && server.hasArg("val")) {
    int id = server.arg("id").toInt();
    int val = constrain(server.arg("val").toInt(), 0, 180);
    if (id >= 0 && id < NUM_SERVOS) {
      targetPos[id] = val; // Set target only, non-blocking interpolator will ease to it
    }
    server.send(200, "text/plain", "OK");
  } else {
    server.send(400, "text/plain", "Bad Request");
  }
}

void handleStatus() {
  bool moving = false;
  String json = "{\"current\":[";
  for (int i = 0; i < NUM_SERVOS; i++) {
    if (i > 0) json += ",";
    json += String(currentPos[i], 1);
    moving = moving || abs(currentPos[i] - targetPos[i]) > 0.1;
  }
  json += "],\"target\":[";
  for (int i = 0; i < NUM_SERVOS; i++) {
    if (i > 0) json += ",";
    json += String(targetPos[i], 1);
  }
  json += "],\"moving\":";
  json += moving ? "true}" : "false}";
  server.send(200, "application/json", json);
}

void handleCmd() {
  if (server.hasArg("act")) {
    String act = server.arg("act");
    if (act == "home") {
      for (int i = 0; i < NUM_SERVOS; i++) {
        targetPos[i] = HOME_ANGLES[i];
      }
    } else if (act == "open") {
      targetPos[5] = 30; // Open claw
    } else if (act == "close") {
      targetPos[5] = 120; // Grip object
    } else {
      server.send(400, "text/plain", "Unknown action");
      return;
    }
    server.send(200, "text/plain", "OK");
  } else {
    server.send(400, "text/plain", "Missing action");
  }
}

// ================= 6. NON-BLOCKING MOTION EASING =============
void updateSmoothMotion() {
  unsigned long now = millis();
  if (now - lastUpdate < UPDATE_INTERVAL_MS) return;
  lastUpdate = now;

  for (int i = 0; i < NUM_SERVOS; i++) {
    if (abs(currentPos[i] - targetPos[i]) > 0.1) {
      float step = STEP_SPEED[i];
      if (currentPos[i] < targetPos[i]) {
        currentPos[i] = min(currentPos[i] + step, targetPos[i]);
      } else {
        currentPos[i] = max(currentPos[i] - step, targetPos[i]);
      }
      servos[i].write((int)round(currentPos[i]));
    }
  }
}

// ================= 7. SETUP & LOOP ===========================
void setup() {
  Serial.begin(115200);
  delay(1000);

  // Initialize positions to locked calibrated Home Pose
  for (int i = 0; i < NUM_SERVOS; i++) {
    currentPos[i] = HOME_ANGLES[i];
    targetPos[i]  = HOME_ANGLES[i];
  }

  // Allocate 4 hardware PWM timers on ESP32
  ESP32PWM::allocateTimer(0);
  ESP32PWM::allocateTimer(1);
  ESP32PWM::allocateTimer(2);
  ESP32PWM::allocateTimer(3);

  // Initialize and attach all 6 servos
  for (int i = 0; i < NUM_SERVOS; i++) {
    servos[i].setPeriodHertz(50);
    servos[i].attach(SERVO_PINS[i], 500, 2400);
    servos[i].write((int)currentPos[i]); // Move directly to home on cold boot
  }

  // Start pure Wi-Fi Hotspot mode
  WiFi.mode(WIFI_AP);
  WiFi.softAPConfig(local_IP, gateway, subnet);
  WiFi.softAP(AP_SSID, AP_PASS);

  Serial.println("\n==============================================");
  Serial.println("  ROBOTIC ARM READY (CALIBRATED HOME LOADED)  ");
  Serial.println("==============================================");
  Serial.print("1. Connect Phone to Wi-Fi : "); Serial.println(AP_SSID);
  Serial.print("3. Browser URL            : http://"); Serial.println(WiFi.softAPIP());
  Serial.println("==============================================\n");

  server.on("/", handleRoot);
  server.on("/status", HTTP_GET, handleStatus);
  server.on("/set", handleSet);
  server.on("/cmd", handleCmd);
  server.begin();
}

void loop() {
  server.handleClient(); // Process incoming web requests
  updateSmoothMotion();  // Gradually step each servo towards target every 15ms
}
