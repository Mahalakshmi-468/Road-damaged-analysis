# ROADGUARD AI — Model Weights Directory

This directory hosts the computer vision weights used for real-time road damage detection and distress classification.

## Supported Model Formats
- **PyTorch YOLOv8 / YOLOv11 weights**: `.pt` (e.g., `road_damage_best.pt`, `yolov8n-rdd.pt`)
- **ONNX weights**: `.onnx` (for optimized CPU inference with ONNXRuntime)

## Standard Damage Categories (RDD2020 / RDD2022 Benchmark Taxonomy)
When a Road Damage Dataset (RDD) model is loaded, it detects:
1. `D00` — Longitudinal Crack (Wheel path & centerline cracks)
2. `D10` — Transverse Crack (Perpendicular thermal/joint cracks)
3. `D20` — Alligator Crack / Fatigue Cracking (Interconnected mesh cracks)
4. `D40` — Pothole (Structural cavity / localized surface depression)
5. `Rutting` — Lateral depression along wheel tracks
6. `Manhole / Patch` — Surface elevation anomalies

## Default Behavior
- If `models/road_damage_best.pt` or another configured `.pt` file is placed in this folder, RoadGuard AI automatically loads it with `ultralytics.YOLO` on startup or via the Model Configuration reload API.
- If no custom weights file is present, RoadGuard AI switches seamlessly to the **RoadGuard Computer Vision Distress Engine**.
  - **No fake bounding boxes!** The CV engine executes real OpenCV edge gradient, adaptive thresholding, asphalt texture variance analysis, and contour aspect ratio geometry to detect structural asphalt irregularities, potholes, and surface cracks.
  - The System Health page, API responses, and reports explicitly state the active detection engine and supported classes.

## How to Download Pre-Trained RDD2020 / RDD2022 Weights
You can place any YOLOv8 model trained on the Crowdsensing Road Damage Detection challenge (RDD) directly into this folder:
```bash
# Example download of a pre-trained RDD2020 YOLO model:
# Place the file as:
# models/road_damage_best.pt
```
Then restart the backend or hit `POST /api/v1/health/model/reload`.
