# ROADGUARD AI — Architecture Overview

ROADGUARD AI is an enterprise-grade road surface condition assessment and defect intelligence platform built for civil maintenance engineers, smart-city administrators, and inspection teams.

```
+-------------------------------------------------------------------------+
|                              ROADGUARD AI                               |
|                         Full-Stack Architecture                         |
+-------------------------------------------------------------------------+

   [ CLIENT BROWSER ]
           |
           v
   +----------------------------------------------------------------------+
   | React 19 + TypeScript + Vite + Tailwind CSS                          |
   | - Executive Intelligence Dashboard (Recharts telemetry)              |
   | - AI Road Inspection Studio (Canvas, bounding box inspector)         |
   | - Geospatial Intelligence Map (Leaflet / OpenStreetMap)              |
   | - Inspection Registry (Filters, search, pagination)                  |
   | - Human Reviewer Decisions (Override severity & audit notes)         |
   | - Reports & Export Center (PDF certificates, CSV, JSON)              |
   +----------------------------------------------------------------------+
           |
           | HTTP / REST API (Port 8000 / Proxy 5173)
           v
   +----------------------------------------------------------------------+
   | FastAPI REST Backend Server (Python 3.12)                            |
   |                                                                      |
   |  /api/v1/health       - Health check & model reload                  |
   |  /api/v1/inspections  - Upload, inference, CRUD, reviewer patch      |
   |  /api/v1/analytics    - Empirical KPIs & distribution aggregates     |
   |  /api/v1/reports      - Streaming PDF generator, CSV & JSON exports  |
   +----------------------------------------------------------------------+
        |            |                          |
        v            v                          v
 +------------+ +---------------------------+ +---------------------------+
 | SQLite /   | | AI Detection Engine       | | File Storage Subsystem    |
 | PostgreSQL | | - Mode A: YOLOv8 PyTorch  | | - storage/uploads         |
 | (SQLAlchemy| |   (RDD road damage weights| | - storage/annotated       |
 |  ORM)      | | - Mode B: CV Surface      | | - storage/reports         |
 |            | |   Distress Analyzer       | |                           |
 |            | |   (Deterministic OpenCV)  | |                           |
 +------------+ +---------------------------+ +---------------------------+
```

## Core Modules & Design Rationale

### 1. Dual-Mode Detection Engine
- **Mode A (Deep Learning YOLO)**: When custom weights trained on the Road Damage Dataset (`.pt` or `.onnx`) are placed in `models/`, the engine loads them via `ultralytics.YOLO`. It automatically inspects the class dictionary and verifies that road distress classes exist before using them.
- **Mode B (RoadGuard Computer Vision Distress Engine)**: If custom weights are not present, RoadGuard uses deterministic OpenCV computer vision algorithms (bilateral filtering, edge gradients, morphological closing, contour compactness, and aspect ratio analysis) to detect actual surface defects, cavities, and cracks. **It never fabricates fake detections or random boxes.**
- **Transparent Telemetry**: The active engine, model identifier, hardware acceleration device (CPU/CUDA), and confidence cutoff are always broadcast via `/api/v1/health` and displayed across all client views.

### 2. Rule-Based Severity Heuristic
RoadGuard computes an objective Distress Index ($0 - 100$) based on:
1. Multiplicity of defects (number of detected distress instances)
2. Defect category structural weights (Potholes $1.5$, Alligator Cracks $1.4$, Rutting $1.2$, Longitudinal Cracks $1.0$, Transverse Cracks $0.85$)
3. Aggregate road surface area ratio occupied by the defects
4. Detection confidence scores

### 3. Human-In-The-Loop Verification
Civil engineers can:
- Transition lifecycle status: `PENDING` $\to$ `REVIEWED` or `NEEDS_REINSPECTION`
- Override severity rating with justification while preserving original AI assessment
- Add official field notes
