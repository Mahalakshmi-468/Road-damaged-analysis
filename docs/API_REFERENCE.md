# ROADGUARD AI — REST API Reference

The backend exposes a complete OpenAPI 3.0 specification available interactively at `http://127.0.0.1:8000/docs`.

All endpoints are prefixed with `/api/v1`.

---

## 1. System Health
- **`GET /api/v1/health`**
  - Returns backend connectivity, database status, loaded model identifier, active device (CPU/CUDA), and supported defect classes.
- **`POST /api/v1/health/model/reload`**
  - Hot-reloads model weights path or adjusts confidence/IoU cutoffs dynamically.

---

## 2. Inspections
- **`POST /api/v1/inspections/upload-and-detect`**
  - Accepts `multipart/form-data`: `file`, `title`, `latitude`, `longitude`, `location_name`, `confidence_threshold`.
  - Performs image validation, auto-extracts EXIF GPS if present, runs real inference, computes rule-based severity, saves annotated image with bounding boxes, and commits record.
- **`GET /api/v1/inspections`**
  - Lists inspections with query parameters: `page`, `limit`, `severity`, `status`, `search`, `has_gps`, `sort_by`.
- **`GET /api/v1/inspections/{id}`**
  - Retrieves single inspection with all detected defect coordinates and bounding boxes.
- **`PATCH /api/v1/inspections/{id}`**
  - Human reviewer update: `status` (`PENDING`, `REVIEWED`, `NEEDS_REINSPECTION`), `manual_severity` (`LOW`, `MEDIUM`, `HIGH`, `UNKNOWN`, or `RESET`), `reviewer_notes`.
- **`DELETE /api/v1/inspections/{id}`**
  - Deletes inspection record and associated image files on disk.

---

## 3. Analytics
- **`GET /api/v1/analytics/dashboard`**
  - Returns calculated metrics directly from database: total inspections, total damages, high severity count, pending verification count, verified count, trends over time, category frequencies, severity distribution, and confidence histogram.

---

## 4. Reports & Exports
- **`GET /api/v1/reports/inspections/{id}/pdf`**
  - Generates and streams an official printable PDF inspection certificate.
- **`GET /api/v1/reports/export/csv`**
  - Exports archival CSV spreadsheet.
- **`GET /api/v1/reports/export/json`**
  - Exports structured JSON manifest.
