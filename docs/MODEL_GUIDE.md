# ROADGUARD AI — Model Weights and Computer Vision Guide

## Overview

ROADGUARD AI implements a strict honesty policy regarding AI predictions:
- Generic COCO pretrained models (which detect people, cars, dogs) **are never falsely claimed to detect potholes or road cracks**.
- Simulated random bounding boxes are strictly prohibited.

Instead, ROADGUARD AI employs a dual-engine architecture:

---

### Engine 1: Road Damage Deep Learning Model (YOLO)
When specialized weights are loaded into `models/road_damage_best.pt`:
- **Supported Formats**: PyTorch `.pt` or ONNX `.onnx`.
- **Benchmark Training**: Trained on RDD2020 / RDD2022 (Crowdsensing Road Damage Detection Challenge).
- **Recognized Class Names**:
  - `D00` / `crack`: Longitudinal Crack
  - `D10` / `transverse_crack`: Transverse Crack
  - `D20` / `alligator_crack`: Alligator Crack (Fatigue failure)
  - `D40` / `pothole`: Pothole Cavity
  - `rutting`: Wheel Track Depression

### How to Install Custom Weights
1. Obtain or train an Ultralytics YOLOv8/v11 model on the Road Damage Dataset.
2. Copy the exported `.pt` file to:
   ```
   roadguard-ai/models/road_damage_best.pt
   ```
3. Open the **System & Model Health** page in the web dashboard and click **Hot-Reload Engine Weights**, or call:
   ```http
   POST /api/v1/health/model/reload
   {
     "weights_path": "./models/road_damage_best.pt"
   }
   ```

---

### Engine 2: RoadGuard Computer Vision Distress Analyzer (Default Active)
If custom weights are absent, RoadGuard automatically activates its internal OpenCV distress analyzer:
1. **Bilateral Filtering**: Preserves sharp defect boundaries while smoothing porous asphalt aggregate grain.
2. **Canny Edge Gradients**: Detects multi-scale surface shear lines.
3. **Morphological Closures**: Bridges fragmented hairline cracks and consolidates depression regions.
4. **Contour Geometry Analysis**:
   - Aspect ratio $< 0.45$: Identified as Longitudinal Crack.
   - Aspect ratio $> 2.2$: Identified as Transverse Crack.
   - Dark cavity with circular/elliptical solidity $> 0.35$: Identified as Pothole.
   - High perimeter and branched network: Identified as Alligator Crack.
5. **Exact Normalization**: Calculates normalized $[x_{min}, y_{min}, x_{max}, y_{max}]$ bounding coordinates and real surface area percentages.
