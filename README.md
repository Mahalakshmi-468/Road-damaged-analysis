# ROADGUARD AI
## Enterprise-Grade AI Road Damage Detection & Smart Infrastructure Intelligence Platform

[![Build Status](https://img.shields.io/badge/Build-Passing-emerald)](http://127.0.0.1:5173)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI_v0.110+-0891b2)](http://127.0.0.1:8000/docs)
[![React](https://img.shields.io/badge/Frontend-React_19_+_Vite-61dafb)](http://127.0.0.1:5173)
[![Computer Vision](https://img.shields.io/badge/AI%20Engine-OpenCV_%26_YOLOv8-blueviolet)](models/README.md)
[![License](https://img.shields.io/badge/License-MIT-slate)](LICENSE)

ROADGUARD AI is an enterprise-grade road surface defect detection and pavement risk assessment platform designed for municipal infrastructure teams, civil maintenance engineers, smart-city administrators, and academic technical demonstrations.

---

## 🏛 Project Highlights

- **B.Tech CSBS Mini-Project & College Exhibition Showcase**: Engineered with enterprise design language, real AI inference, live geospatial tracking, and verifiable database metrics.
- **Dual AI Computer Vision Engine**:
  - **Ultralytics YOLO (PyTorch)**: Native loader for specialized Road Damage Dataset (RDD2020/2022) weights.
  - **RoadGuard Computer Vision Distress Analyzer**: Built-in deterministic OpenCV engine utilizing edge gradient analysis, morphological closures, and contour aspect ratio geometry.
  - **Zero Fabrication**: Never fakes bounding boxes or claims generic COCO models detect potholes.
- **Rule-Based Severity Rating**: Computes an objective Distress Index ($0 - 100$) factoring defect multiplicity, structural hazard weights (potholes & base fatigue cracks), and surface area ratio.
- **Interactive Geospatial Intelligence Map**: Built with React-Leaflet and OpenStreetMap tiles. Displays color-coded severity markers, corridor popups, and a quarantine section for unmapped surveys.
- **Human-in-the-Loop Verification**: Reviewers can override AI severity, transition inspection status (`PENDING` $\to$ `REVIEWED` / `NEEDS_REINSPECTION`), and append field engineering notes.
- **Export Center**: Streams official ReportLab PDF inspection reports, tabular CSV datasets, and structured JSON manifests.

---

## 🚀 Quick Start (Windows Development)

### 1. Prerequisites
- **Python 3.10+** (Tested with Python 3.12.10)
- **Node.js 18+** (Tested with Node.js v22.23.1)

### 2. Start the Backend API Server
Open a terminal in the project directory:
```powershell
cd backend
python -m pip install -r requirements.txt
python seed_data.py    # Seeds realistic road inspection records
python run_backend.py  # Starts server on http://127.0.0.1:8000
```
- **Backend API**: `http://127.0.0.1:8000`
- **Interactive OpenAPI Docs**: `http://127.0.0.1:8000/docs`

### 3. Start the Frontend Application
Open a second terminal:
```powershell
cd frontend
npm install
npm run dev            # Starts Vite on http://127.0.0.1:5173
```
- **Web Dashboard**: `http://127.0.0.1:5173`

---

## 🧪 Automated Testing

Automated unit and integration test suite covering image validation, rule-based severity calculation, health telemetry, and the complete inspection lifecycle:

```powershell
cd backend
python -m pytest tests/ -v
```

Output:
```
tests/test_health.py::test_root_endpoint PASSED                          [ 12%]
tests/test_health.py::test_health_endpoint PASSED                        [ 25%]
tests/test_image_service.py::test_invalid_extension PASSED               [ 37%]
tests/test_image_service.py::test_empty_file PASSED                      [ 50%]
tests/test_inspections_api.py::test_full_inspection_lifecycle PASSED     [ 62%]
tests/test_severity.py::test_empty_detections PASSED                     [ 75%]
tests/test_severity.py::test_single_minor_crack_low_severity PASSED      [ 87%]
tests/test_severity.py::test_multiple_potholes_high_severity PASSED      [100%]
======================== 8 passed in 2.28s ========================
```

To test the frontend production bundle:
```powershell
cd frontend
npm run build
```

---

## 📂 Project Structure

```
roadguard-ai/
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/  # Health, Inspections, Analytics, Reports
│   │   ├── core/              # Config, settings, logging
│   │   ├── database/          # SQLAlchemy engine, session, Base
│   │   ├── models/            # Inspection, Detection ORM models
│   │   ├── schemas/           # Pydantic validation schemas
│   │   ├── services/          # Real AI detector, severity engine, EXIF, PDF generator
│   │   └── main.py            # FastAPI application
│   ├── storage/               # Uploaded images, annotated overlays, reports
│   ├── tests/                 # Pytest test suite
│   ├── seed_data.py           # Database seeder
│   ├── run_backend.py         # Backend launcher
│   └── requirements.txt       # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/        # Dashboard, Studio, Map, Inspections, Analytics
│   │   ├── pages/             # Route views
│   │   ├── services/          # API client
│   │   ├── types/             # TypeScript definitions
│   │   ├── App.tsx            # Main application shell
│   │   └── main.tsx           # React entry point
│   ├── package.json           # Frontend dependencies
│   ├── vite.config.ts         # Vite bundler & backend proxy
│   └── tsconfig.json          # TypeScript configuration
├── models/
│   └── README.md              # Guide for loading custom RDD YOLO weights
├── sample_images/             # Pre-generated road damage samples for 1-click demos
├── docs/
│   ├── ARCHITECTURE.md        # Technical architecture documentation
│   ├── DEPLOYMENT.md          # Production cloud deployment guide
│   ├── MODEL_GUIDE.md         # Weights setup and CV algorithms
│   └── API_REFERENCE.md       # Complete REST API specification
├── .env.example               # Environment variables template
├── .gitignore
└── README.md
```

---

## 🎯 Exhibition Quick-Demo Presets

During a live technical demonstration or exhibition, open the **AI Inspection Studio** and click one of the 1-click preset buttons:
1. **Severe Pothole Sample**: Pothole cavity on Bangalore Outer Ring Road.
2. **Structural Cracks Sample**: Longitudinal & transverse cracks on Anna Salai Corridor, Chennai.
3. **Mixed Pavement Distress**: Combined potholes and fatigue cracks on NH44 Expressway.

The system will instantly load the image, execute real computer vision inference, overlay crisp bounding boxes with confidence meters, generate the engineering severity rationale, and plot the verified coordinates on the geospatial map.

---

## 📜 Academic Attribution

Developed for B.Tech Computer Science and Business Systems (CSBS) Mini-Project & Smart Infrastructure Demonstration.
Licensed under the [MIT License](LICENSE).
