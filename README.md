# Catch Me If U  Can Agent

## Overview

This project builds a fully automated monitoring system for a workspace using AI. The system uses video and audio feeds to detect inappropriate behavior (e.g., unwanted touching, hugging), theft (e.g., stealing chairs or furniture), and offensive language (specifically Egyptian Arabic curse words). All alerts are stored with relevant video/audio clips and shown on a professional admin dashboard.

> **Note**: This project focuses only on the admin side. There is no user-facing app, login, or registration yet, all will be easily implemented later. The goal is for the owner to review alerts and manage the system.

---

## Features

* Real-time human pose estimation to detect inappropriate physical interactions
* Real-time object detection to track unauthorized object removal
* Real-time audio transcription to catch Egyptian curse words
* Admin dashboard with alert history, video/audio playback, and false claim feedback

---

## Tech Stack

* **Language**: Python
* **Frontend/Dashboard**: Reflex (Pure Python, full-stack framework)
* **Computer Vision Models**: YOLOv8, YOLOv7-Pose
* **Speech Recognition**: Wav2Vec2 (Egyptian Arabic model)
* **Video Processing**: OpenCV
* **Audio Processing**: PyDub, Transformers

---

## Models Used (Pre-trained)

### 1. YOLOv7-Pose (for inappropriate body contact)

* Task: Multi-person human pose detection
* Source: [https://github.com/WongKinYiu/yolov7](https://github.com/WongKinYiu/yolov7)
* Weights: [Download YOLOv7-W6-Pose.pt](https://github.com/WongKinYiu/yolov7/releases/download/v0.1/yolov7-w6-pose.pt)

### 2. YOLOv8 (for object/furniture detection)

* Task: Object detection (e.g., chair, kettle, furniture)
* Library: [Ultralytics](https://docs.ultralytics.com/)
* Usage: Detect objects in the room and track movement across frames

### 3. Wav2Vec2 (for speech-to-text, Egyptian Arabic)

* Task: Transcribe microphone audio
* Model: `Zaid/wav2vec2-large-xlsr-53-arabic-egyptian`
* Source: [https://huggingface.co/arabic-nlp/wav2vec2-large-xlsr-53-arabic-egyptian](https://huggingface.co/arabic-nlp/wav2vec2-large-xlsr-53-arabic-egyptian)

---

## Project Structure

```
catch-me-if-u-can/            # 🔹 Root folder = project name
├── backend/                  # 🔧 All server-side logic
│   ├── agent/                # 🤖 AI agent & detection system
│   │   ├── agent.py
│   │   ├── models/
│   │   │   ├── yolov7_pose/
│   │   │   ├── yolov8/
│   │   │   └── wav2vec2/
│   │   ├── utils/
│   │   │   ├── video_processing.py
│   │   │   ├── audio_processing.py
│   │   │   └── alert_manager.py
│   │   └── data/
│   │       ├── videos/
│   │       └── audio/
│
│   ├── api/                  # (Future) API endpoints for mobile/web apps
│
│   └── database/             # (Future) DB schemas, migrations
│       └── models.py
│
├── admin_app/                # 🧑‍💼 Admin-only dashboard
│       └── (your Reflex dashboard code)
│
├── user_app/                 # (Future) User-side mobile or web app
│
├── shared/                   # Shared utilities, configs
│   └── config.py
│
├── requirements.txt
└── README.md

```

---

## Installation

### 1. Clone Repo

```bash
git clone https://github.com/YOUR_USERNAME/workspace_monitor.git
cd workspace_monitor
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate     # Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Download Models

#### YOLOv7-Pose

```bash
mkdir -p models/yolov7_pose
cd models/yolov7_pose
wget https://github.com/WongKinYiu/yolov7/releases/download/v0.1/yolov7-w6-pose.pt
```

#### YOLOv8

```bash
pip install ultralytics
# No manual download needed, YOLOv8 auto-downloads weights
```

#### Wav2Vec2

```bash
pip install transformers librosa
# Model will be loaded from HuggingFace in code
```

---

## How to Run

### 1. Run the Monitoring Agent

```bash
python agent.py
```

This starts processing all camera feeds and microphone input.

### 2. Launch Admin Dashboard (Reflex)

```bash
cd dashboard/reflex_app
reflex run
```

Go to `http://localhost:3000` in your browser to view alerts.

---

## Admin Dashboard Features

* View list of all alerts with timestamps
* Playback video/audio of incident
* Delete or mark as false alert
* Admin feedback logging
* System configuration (thresholds, alert types)

---

## How the Agent Works

1. Captures frames from all cameras
2. Runs YOLOv8 and YOLOv7-Pose models on each frame
3. Runs Wav2Vec2 on mic input every few seconds
4. Checks:

   * Any detected touching/hugging between opposite sex?
   * Any object (e.g. chair, kettle) leaving its zone?
   * Any curse words in Egyptian Arabic?
5. If any behavior is flagged:

   * Saves 10s video/audio clip
   * Generates alert with timestamp and media file
   * Sends alert to dashboard

---

## License

MIT License. Free for personal or commercial use with attribution.

---
## Contact

* Website: [ahmedammar.dev](https://ahmedammar.dev)
* Email: [contact@ahmedammar.dev](mailto:contact@ahmedammar.dev)
