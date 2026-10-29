import json
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import StreamingResponse
import io
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.inspection import Inspection
from app.services.report_service import generate_inspection_pdf, generate_inspections_csv

router = APIRouter()

@router.get("/inspections/{id}/pdf")
def export_inspection_pdf(id: str, db: Session = Depends(get_db)):
    """Generates and streams a professional PDF report for an inspection."""
    inspection = db.query(Inspection).filter(Inspection.id == id).first()
    if not inspection:
        raise HTTPException(status_code=404, detail="Inspection not found.")

    try:
        pdf_bytes = generate_inspection_pdf(inspection)
        filename = f"RoadGuard_Report_{inspection.id[:8]}_{inspection.effective_severity}.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF report: {str(e)}")

@router.get("/export/csv")
def export_all_inspections_csv(db: Session = Depends(get_db)):
    """Exports all inspections as an archival CSV spreadsheet."""
    inspections = db.query(Inspection).order_by(Inspection.created_at.desc()).all()
    csv_text = generate_inspections_csv(inspections)
    return Response(
        content=csv_text,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=roadguard_inspections_export.csv"}
    )

@router.get("/export/json")
def export_all_inspections_json(db: Session = Depends(get_db)):
    """Exports all inspections and their detections as structured JSON."""
    inspections = db.query(Inspection).order_by(Inspection.created_at.desc()).all()
    data = []
    for ins in inspections:
        data.append({
            "id": ins.id,
            "title": ins.title,
            "original_filename": ins.original_filename,
            "created_at": ins.created_at.isoformat(),
            "ai_severity": ins.ai_severity,
            "manual_severity": ins.manual_severity,
            "effective_severity": ins.effective_severity,
            "status": ins.status,
            "reviewer_notes": ins.reviewer_notes,
            "latitude": ins.latitude,
            "longitude": ins.longitude,
            "location_name": ins.location_name,
            "location_source": ins.location_source,
            "model_identifier": ins.model_identifier,
            "inference_ms": ins.inference_ms,
            "damage_count": ins.damage_count,
            "detections": [
                {
                    "class_name": d.class_name,
                    "confidence": d.confidence,
                    "x_min": d.x_min,
                    "y_min": d.y_min,
                    "x_max": d.x_max,
                    "y_max": d.y_max,
                    "area_ratio": d.area_ratio
                } for d in ins.detections
            ]
        })

    return Response(
        content=json.dumps(data, indent=2),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=roadguard_inspections_manifest.json"}
    )
