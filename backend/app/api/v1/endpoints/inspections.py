import os
import cv2
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, asc

from app.database.session import get_db
from app.models.inspection import Inspection
from app.models.detection import Detection
from app.schemas.inspection import (
    InspectionResponse,
    InspectionListResponse,
    InspectionReviewUpdate,
    DetectionResponse
)
from app.services.image_service import (
    validate_uploaded_image,
    save_original_image,
    render_annotated_image
)
from app.services.detector import detection_engine
from app.services.severity import calculate_severity_assessment
from app.services.exif import extract_exif_metadata
from app.core.logging import logger

router = APIRouter()

def _format_inspection_response(ins: Inspection) -> InspectionResponse:
    return InspectionResponse(
        id=ins.id,
        title=ins.title,
        original_filename=ins.original_filename,
        image_url=f"/{ins.image_path.replace(chr(92), '/')}",
        annotated_image_url=f"/{ins.annotated_image_path.replace(chr(92), '/')}",
        image_width=ins.image_width,
        image_height=ins.image_height,
        file_size_bytes=ins.file_size_bytes,
        mime_type=ins.mime_type,
        latitude=ins.latitude,
        longitude=ins.longitude,
        location_name=ins.location_name,
        location_source=ins.location_source,
        ai_severity=ins.ai_severity,
        manual_severity=ins.manual_severity,
        effective_severity=ins.effective_severity,
        severity_rationale=ins.severity_rationale,
        status=ins.status,
        reviewer_notes=ins.reviewer_notes,
        reviewed_at=ins.reviewed_at,
        model_identifier=ins.model_identifier,
        inference_ms=ins.inference_ms,
        damage_count=ins.damage_count,
        created_at=ins.created_at,
        updated_at=ins.updated_at,
        detections=[
            DetectionResponse(
                id=d.id,
                inspection_id=d.inspection_id,
                class_name=d.class_name,
                confidence=d.confidence,
                x_min=d.x_min,
                y_min=d.y_min,
                x_max=d.x_max,
                y_max=d.y_max,
                area_ratio=d.area_ratio,
                is_verified=d.is_verified,
                created_at=d.created_at
            ) for d in ins.detections
        ]
    )

@router.post("/upload-and-detect", response_model=InspectionResponse)
async def upload_and_detect_inspection(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),
    location_name: Optional[str] = Form(None),
    confidence_threshold: Optional[float] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Primary RoadGuard Inspection Studio pipeline:
    1. Validates image type, integrity, and size.
    2. Stores original image safely.
    3. Auto-extracts GPS metadata from EXIF if manual coordinates not provided.
    4. Executes real computer vision / deep learning inference.
    5. Computes transparent rule-based severity rating and rationale.
    6. Generates annotated image with precise bounding box overlays.
    7. Commits inspection and detection manifest to persistent database.
    """
    # 1. Validation
    file_bytes, ext = validate_uploaded_image(file)
    original_filename = file.filename or f"inspection{ext}"

    # 2. Save original
    rel_orig_path, abs_orig_path, width, height = save_original_image(file_bytes, ext)

    # 3. Handle GPS coordinates
    loc_source = "NONE"
    lat_val = latitude
    lon_val = longitude

    if lat_val is not None and lon_val is not None:
        loc_source = "MANUAL"
    else:
        # Check EXIF
        exif_info = extract_exif_metadata(abs_orig_path)
        if exif_info.get("has_gps") and exif_info.get("latitude") and exif_info.get("longitude"):
            lat_val = exif_info["latitude"]
            lon_val = exif_info["longitude"]
            loc_source = "GPS_EXIF"

    # 4. Run real inference
    img_bgr = cv2.imread(abs_orig_path)
    if img_bgr is None:
        raise HTTPException(status_code=500, detail="Failed to load image for CV inference.")

    conf_thresh = confidence_threshold if confidence_threshold is not None else detection_engine.confidence_threshold
    raw_detections, inference_ms = detection_engine.detect(img_bgr, conf_override=conf_thresh)

    # 5. Rule-based severity assessment
    severity_label, rationale = calculate_severity_assessment(raw_detections)

    # 6. Render annotated output image
    annotated_filename = f"annotated_{Path(rel_orig_path).name}"
    rel_annot_path, abs_annot_path = render_annotated_image(
        original_path=abs_orig_path,
        detections=raw_detections,
        output_filename=annotated_filename
    )

    # 7. Commit to DB
    clean_title = title.strip() if title and title.strip() else f"Inspection {original_filename}"
    inspection = Inspection(
        title=clean_title,
        original_filename=original_filename,
        image_path=rel_orig_path,
        annotated_image_path=rel_annot_path,
        image_width=width,
        image_height=height,
        file_size_bytes=len(file_bytes),
        mime_type=file.content_type or "image/jpeg",
        latitude=lat_val,
        longitude=lon_val,
        location_name=location_name.strip() if location_name else None,
        location_source=loc_source,
        ai_severity=severity_label,
        manual_severity=None,
        severity_rationale=rationale,
        status="PENDING",
        model_identifier=detection_engine.model_identifier,
        inference_ms=inference_ms,
        damage_count=len(raw_detections)
    )
    db.add(inspection)
    db.flush()

    for d in raw_detections:
        detection_entry = Detection(
            inspection_id=inspection.id,
            class_name=d["class_name"],
            confidence=d["confidence"],
            x_min=d["x_min"],
            y_min=d["y_min"],
            x_max=d["x_max"],
            y_max=d["y_max"],
            area_ratio=d["area_ratio"],
            is_verified=True
        )
        db.add(detection_entry)

    db.commit()
    db.refresh(inspection)

    logger.info(f"Created inspection {inspection.id}: {len(raw_detections)} damages, severity: {severity_label}")
    return _format_inspection_response(inspection)

@router.get("", response_model=InspectionListResponse)
def list_inspections(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    severity: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    has_gps: Optional[bool] = Query(None),
    sort_by: str = Query("created_at_desc"),
    db: Session = Depends(get_db)
):
    """
    Search and filter inspection records with pagination.
    """
    query = db.query(Inspection)

    if severity:
        sev_upper = severity.upper()
        query = query.filter(
            or_(
                Inspection.manual_severity == sev_upper,
                (Inspection.manual_severity == None) & (Inspection.ai_severity == sev_upper)
            )
        )

    if status:
        query = query.filter(Inspection.status == status.upper())

    if has_gps is not None:
        if has_gps:
            query = query.filter(Inspection.latitude.isnot(None), Inspection.longitude.isnot(None))
        else:
            query = query.filter(or_(Inspection.latitude.is_(None), Inspection.longitude.is_(None)))

    if search:
        search_fmt = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Inspection.title.ilike(search_fmt),
                Inspection.original_filename.ilike(search_fmt),
                Inspection.location_name.ilike(search_fmt),
                Inspection.reviewer_notes.ilike(search_fmt)
            )
        )

    # Sorting
    if sort_by == "created_at_asc":
        query = query.order_by(asc(Inspection.created_at))
    elif sort_by == "damage_desc":
        query = query.order_by(desc(Inspection.damage_count))
    else:
        query = query.order_by(desc(Inspection.created_at))

    total = query.count()
    offset = (page - 1) * limit
    items = query.offset(offset).limit(limit).all()

    return InspectionListResponse(
        total=total,
        page=page,
        limit=limit,
        items=[_format_inspection_response(ins) for ins in items]
    )

@router.get("/{id}", response_model=InspectionResponse)
def get_inspection_detail(id: str, db: Session = Depends(get_db)):
    """Retrieve detailed inspection record with bounding box detections."""
    inspection = db.query(Inspection).filter(Inspection.id == id).first()
    if not inspection:
        raise HTTPException(status_code=404, detail="Inspection not found.")
    return _format_inspection_response(inspection)

@router.patch("/{id}", response_model=InspectionResponse)
def update_inspection_review(
    id: str,
    payload: InspectionReviewUpdate,
    db: Session = Depends(get_db)
):
    """
    Human Reviewer Interface:
    Allows civil engineers / inspectors to:
    - Override severity classification (preserving original AI estimation)
    - Transition inspection state (PENDING -> REVIEWED / NEEDS_REINSPECTION)
    - Add reviewer field notes
    """
    inspection = db.query(Inspection).filter(Inspection.id == id).first()
    if not inspection:
        raise HTTPException(status_code=404, detail="Inspection not found.")

    if payload.status:
        st = payload.status.upper()
        if st not in ["PENDING", "REVIEWED", "NEEDS_REINSPECTION"]:
            raise HTTPException(status_code=400, detail="Invalid status transition.")
        inspection.status = st

    if payload.manual_severity is not None:
        if payload.manual_severity == "" or payload.manual_severity.upper() == "RESET":
            inspection.manual_severity = None
        else:
            sev = payload.manual_severity.upper()
            if sev not in ["LOW", "MEDIUM", "HIGH", "UNKNOWN"]:
                raise HTTPException(status_code=400, detail="Invalid severity level.")
            inspection.manual_severity = sev

    if payload.reviewer_notes is not None:
        inspection.reviewer_notes = payload.reviewer_notes

    inspection.reviewed_at = datetime.utcnow()
    inspection.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(inspection)
    logger.info(f"Updated review for inspection {id}: status={inspection.status}, manual_sev={inspection.manual_severity}")
    return _format_inspection_response(inspection)

@router.delete("/{id}")
def delete_inspection(id: str, db: Session = Depends(get_db)):
    """Deletes inspection record and associated uploaded/annotated image files."""
    inspection = db.query(Inspection).filter(Inspection.id == id).first()
    if not inspection:
        raise HTTPException(status_code=404, detail="Inspection not found.")

    # Remove files if present
    for path_str in [inspection.image_path, inspection.annotated_image_path]:
        try:
            full_p = Path(path_str)
            if full_p.exists():
                full_p.unlink()
        except Exception as e:
            logger.warning(f"Failed to delete file {path_str}: {e}")

    db.delete(inspection)
    db.commit()
    return {"success": True, "message": f"Inspection {id} and files deleted successfully."}
