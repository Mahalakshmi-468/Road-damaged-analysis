import os
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))

from app.database.session import SessionLocal, Base, engine
from app.models.inspection import Inspection
from app.models.detection import Detection
from app.services.detector import detection_engine
from app.services.severity import calculate_severity_assessment
from app.services.image_service import save_original_image, render_annotated_image
import cv2

def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    count = db.query(Inspection).count()
    if count > 2:
        print(f"Database already populated with {count} inspections. Skipping seed.")
        db.close()
        return

    sample_dir = backend_dir.parent / "sample_images"
    sample_files = [
        {
            "filename": "pothole_sample_1.jpg",
            "title": "Outer Ring Road Sector 3 - Pothole Hazard",
            "lat": 12.9716,
            "lon": 77.5946,
            "loc": "Outer Ring Road, Bengaluru",
            "status": "REVIEWED",
            "notes": "Verified severe cavity. Maintenance crew dispatched for cold asphalt infill.",
            "manual_sev": "HIGH"
        },
        {
            "filename": "crack_sample_1.jpg",
            "title": "Anna Salai Arterial - Longitudinal Fatigue",
            "lat": 13.0827,
            "lon": 80.2707,
            "loc": "Anna Salai Corridor, Chennai",
            "status": "REVIEWED",
            "notes": "Surface crack sealed. Scheduled for routine crack sealing treatment.",
            "manual_sev": "MEDIUM"
        },
        {
            "filename": "mixed_damage_sample.jpg",
            "title": "NH44 Northbound Lane 2 - Mixed Pavement Distress",
            "lat": 17.3850,
            "lon": 78.4867,
            "loc": "NH44 Expressway Corridor, Hyderabad",
            "status": "PENDING",
            "notes": "Automated drone survey capture. Awaiting civil engineer review.",
            "manual_sev": None
        },
        {
            "filename": "pothole_sample_1.jpg",
            "title": "Rural Arterial Route 14 (Unmapped Survey)",
            "lat": None,
            "lon": None,
            "loc": "Unsurveyed Rural Sector",
            "status": "NEEDS_REINSPECTION",
            "notes": "GPS EXIF missing from imagery. Requires manual location triangulation.",
            "manual_sev": None
        }
    ]

    for item in sample_files:
        src_path = sample_dir / item["filename"]
        if not src_path.exists():
            continue

        with open(src_path, "rb") as f:
            file_bytes = f.read()

        rel_orig, abs_orig, width, height = save_original_image(file_bytes, ".jpg")
        img_bgr = cv2.imread(abs_orig)
        raw_dets, inf_ms = detection_engine.detect(img_bgr, conf_override=0.20)
        sev_label, rationale = calculate_severity_assessment(raw_dets)

        annot_filename = f"annotated_{Path(rel_orig).name}"
        rel_annot, _ = render_annotated_image(abs_orig, raw_dets, annot_filename)

        ins = Inspection(
            title=item["title"],
            original_filename=item["filename"],
            image_path=rel_orig,
            annotated_image_path=rel_annot,
            image_width=width,
            image_height=height,
            file_size_bytes=len(file_bytes),
            mime_type="image/jpeg",
            latitude=item["lat"],
            longitude=item["lon"],
            location_name=item["loc"],
            location_source="MANUAL" if item["lat"] else "NONE",
            ai_severity=sev_label,
            manual_severity=item["manual_sev"],
            severity_rationale=rationale,
            status=item["status"],
            reviewer_notes=item["notes"],
            model_identifier=detection_engine.model_identifier,
            inference_ms=inf_ms,
            damage_count=len(raw_dets)
        )
        db.add(ins)
        db.flush()

        for d in raw_dets:
            det = Detection(
                inspection_id=ins.id,
                class_name=d["class_name"],
                confidence=d["confidence"],
                x_min=d["x_min"],
                y_min=d["y_min"],
                x_max=d["x_max"],
                y_max=d["y_max"],
                area_ratio=d["area_ratio"],
                is_verified=True
            )
            db.add(det)

    db.commit()
    print("Seed complete. Added realistic road damage inspection records.")
    db.close()

if __name__ == "__main__":
    seed()
