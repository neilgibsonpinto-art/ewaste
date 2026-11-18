import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

pdf_path = r"c:\Users\Neil Gibson Pinto\Documents\antigravity\magical-volta\Smart_EWaste_Segregation_Manual.pdf"

doc = SimpleDocTemplate(
    pdf_path,
    pagesize=letter,
    rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40
)

styles = getSampleStyleSheet()

title_style = ParagraphStyle(
    'DocTitle',
    parent=styles['Heading1'],
    fontSize=22,
    leading=26,
    textColor=colors.HexColor('#0284c7'),
    spaceAfter=6,
    alignment=1
)
subtitle_style = ParagraphStyle(
    'DocSub',
    parent=styles['Normal'],
    fontSize=11,
    leading=14,
    textColor=colors.HexColor('#475569'),
    spaceAfter=15,
    alignment=1
)
h1_style = ParagraphStyle(
    'SectionH1',
    parent=styles['Heading2'],
    fontSize=13,
    leading=17,
    textColor=colors.HexColor('#0f172a'),
    spaceBefore=12,
    spaceAfter=6
)
body_style = ParagraphStyle(
    'Body',
    parent=styles['Normal'],
    fontSize=9.5,
    leading=13.5,
    textColor=colors.HexColor('#1e293b')
)
code_style = ParagraphStyle(
    'CodeBlock',
    parent=styles['Code'],
    fontSize=8.5,
    leading=11.5,
    fontName='Courier',
    textColor=colors.HexColor('#0f172a'),
    backColor=colors.HexColor('#f1f5f9'),
    borderPadding=6,
    spaceBefore=4,
    spaceAfter=6
)

story = []

# Title & Subtitle
story.append(Paragraph('Smart E-Waste Segregation System', title_style))
story.append(Paragraph('Complete User and Operations Manual | YOLOv8 + ESP32 6-DOF Robotic Arm', subtitle_style))
story.append(HRFlowable(width='100%', thickness=1.5, color=colors.HexColor('#0284c7'), spaceAfter=10))

# 1. Project Overview
story.append(Paragraph('1. Project Overview', h1_style))
story.append(Paragraph(
    'This system automates electronic waste sorting along a conveyor belt. A computer vision camera running a '
    'custom-trained <b>YOLOv8-Nano</b> deep learning model localizes and identifies e-waste items (<b>PCBs</b>, '
    '<b>Lithium Batteries</b>, and <b>Displays</b>), updates an on-screen tally counter, and transmits wireless HTTP '
    'sorting commands to an <b>ESP32-driven 6-DOF robotic arm</b> to sort each item into its respective bin.',
    body_style
))
story.append(Spacer(1, 6))

# 2. Hardware Architecture & Pinout Table
story.append(Paragraph('2. Hardware Pinout and Wiring (ESP32 Controller)', h1_style))
pin_data = [
    ['Joint Number and Name', 'ESP32 GPIO', 'Servo Model', 'Calibrated Role / Motion'],
    ['Joint 0: Base (Waist)', 'GPIO 13', 'TD-8120MG 20KG', 'Horizontal Pivot: 90 deg (Conveyor) to 0 deg (Bin)'],
    ['Joint 1: Shoulder', 'GPIO 12', 'TD-8120MG 20KG', 'Vertical Column: 75 deg (Home) to 84 deg (Pick)'],
    ['Joint 2: Elbow', 'GPIO 4', 'Metal Gear Servo', 'Arm Forearm Fold: 115 deg (Home) to 124 deg (Pick)'],
    ['Joint 3: Wrist Pitch', 'GPIO 27', 'Standard Servo', 'Vertical Claw Angle: 60 deg (Home) to 80 deg (Pick)'],
    ['Joint 4: Wrist Roll', 'GPIO 26', 'Standard Servo', 'Claw Axial Rotation: 90 deg (Neutral) to 122 deg'],
    ['Joint 5: Gripper Claw', 'GPIO 25', 'Micro / Metal Gear', 'End Effector: 30 deg (Open) to 131 deg (Grip)']
]
t_pins = Table(pin_data, colWidths=[125, 75, 110, 220])
t_pins.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0284c7')),
    ('TEXTCOLOR', (0,0), (-1,0), colors.white),
    ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
    ('FONTSIZE', (0,0), (-1,-1), 8),
    ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ('TOPPADDING', (0,0), (-1,-1), 3),
    ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
    ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f8fafc')])
]))
story.append(t_pins)
story.append(Spacer(1, 8))

# 3. Calibrated Positions Summary
story.append(Paragraph('3. Calibrated Motion Coordinates', h1_style))
pose_data = [
    ['Operation Stance', 'Base', 'Shoulder', 'Elbow', 'Wrist Pitch', 'Wrist Roll', 'Claw'],
    ['Home (Resting Pose)', '90 deg', '75 deg', '115 deg', '60 deg', '90 deg', '45 deg (Relaxed)'],
    ['Conveyor Pick Stance', '99 deg', '84 deg', '124 deg', '80 deg', '122 deg', '131 deg (Firm Grip)'],
    ['Bin Place Stance', '0 deg', '110 deg', '124 deg', '80 deg', '122 deg', '30 deg (Release)']
]
t_poses = Table(pose_data, colWidths=[130, 65, 65, 65, 65, 65, 75])
t_poses.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#334155')),
    ('TEXTCOLOR', (0,0), (-1,0), colors.white),
    ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
    ('FONTSIZE', (0,0), (-1,-1), 8),
    ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ('TOPPADDING', (0,0), (-1,-1), 3),
    ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
    ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f8fafc')])
]))
story.append(t_poses)

# Page Break for Instructions
story.append(PageBreak())

story.append(Paragraph('4. Quickstart: Installation and Execution', h1_style))
story.append(Paragraph('<b>Step 1: Clone the GitHub Repository</b>', body_style))
story.append(Paragraph('git clone https://github.com/neilgibsonpinto-art/ewaste.git<br/>cd ewaste', code_style))

story.append(Paragraph('<b>Step 2: Environment Setup and Dependencies</b>', body_style))
story.append(Paragraph(
    '# Windows PowerShell:<br/>'
    'python -m venv ewaste_env<br/>'
    '.\\ewaste_env\\Scripts\\activate<br/>'
    'pip install -r requirements.txt<br/><br/>'
    '# Mac / Linux Terminal:<br/>'
    'python3 -m venv ewaste_env<br/>'
    'source ewaste_env/bin/activate<br/>'
    'pip install -r requirements.txt',
    code_style
))
story.append(Spacer(1, 6))

story.append(Paragraph('5. Operating Modes', h1_style))
story.append(Paragraph('<b>Mode A: Standalone Webcam Detection and Live Counter (No Hardware Required)</b>', body_style))
story.append(Paragraph(
    'Allows any user to test the AI model on their laptop webcam without the robot arm.<br/>'
    '1. In <code>scripts/detect_live_yolo.py</code>, set <code>TRIGGER_ARM = False</code>.<br/>'
    '2. Run: <code>python scripts/detect_live_yolo.py</code><br/>'
    '3. Hold a PCB, battery, or display in the yellow box to increment live on-screen counters.<br/>'
    '4. Press <b>[r]</b> to reset tallies | Press <b>[q]</b> or <b>[ESC]</b> to exit.',
    body_style
))
story.append(Spacer(1, 6))

story.append(Paragraph('<b>Mode B: Wi-Fi Manual Arm Control via Phone / Browser Dashboard</b>', body_style))
story.append(Paragraph(
    '1. Power on the robot arm 12V battery.<br/>'
    '2. Connect phone/laptop to Wi-Fi: <b>RoboArm-Hotspot</b> (Password: <code>12345678</code>).<br/>'
    '3. Open browser and go to <code>http://192.168.4.1</code>.<br/>'
    '4. Move joint sliders or press <b>RUN AUTO PICK AND PLACE</b> for an automated sorting test cycle.',
    body_style
))
story.append(Spacer(1, 6))

story.append(Paragraph('<b>Mode C: Fully Autonomous Conveyor Sorting (End-to-End)</b>', body_style))
story.append(Paragraph(
    '1. Connect the computer running detection to the <b>RoboArm-Hotspot</b> Wi-Fi.<br/>'
    '2. In <code>scripts/detect_live_yolo.py</code>, ensure <code>TRIGGER_ARM = True</code>.<br/>'
    '3. Run: <code>python scripts/detect_live_yolo.py</code>.<br/>'
    '4. When an item remains stable in the Pick Zone for 4 consecutive frames, the arm automatically grips, lifts, pivots, drops into the bin, and returns to home position.',
    body_style
))
story.append(Spacer(1, 8))

# 6. Troubleshooting
story.append(Paragraph('6. Troubleshooting and Diagnostics', h1_style))
trouble_data = [
    ['Symptom', 'Probable Cause', 'Corrective Action'],
    ['No module named ultralytics', 'Environment not activated', 'Run ewaste_env\\Scripts\\activate before running script'],
    ['Camera cannot be opened', 'Incorrect camera index', 'Change CAMERA_INDEX = 1 in detect_live_yolo.py'],
    ['Arm not responding to camera', 'Wi-Fi not connected', 'Ensure PC is connected to RoboArm-Hotspot Wi-Fi'],
    ['Unwanted background detection', 'Object outside zone', 'Keep item inside yellow CONVEYOR PICK ZONE rectangle']
]
t_trouble = Table(trouble_data, colWidths=[140, 140, 250])
t_trouble.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0284c7')),
    ('TEXTCOLOR', (0,0), (-1,0), colors.white),
    ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
    ('FONTSIZE', (0,0), (-1,-1), 8),
    ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ('TOPPADDING', (0,0), (-1,-1), 3),
    ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
    ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f8fafc')])
]))
story.append(t_trouble)

doc.build(story)
print(f'PDF successfully generated at: {pdf_path}')
