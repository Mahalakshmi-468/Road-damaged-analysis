from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database.session import get_db
from app.models.inspection import Inspection
from app.services.detector import detection_engine
from app.schemas.health import SystemHealthResponse, ModelReloadRequest, ModelReloadResponse
from app.core.config import settings

router = APIRouter()

@router.get("", response_model=SystemHealthResponse)
def get_system_health(db: Session = Depends(get_db)):
    """
    Returns live system, database, and computer vision model operational telemetry.
    Never reports model as operational if it has failed to initialize.
    """
    # Test DB connection
    db_connected = False
    total_inspections = 0
    try:
        db.execute(text("SELECT 1"))
        db_connected = True
        total_inspections = db.query(Inspection).count()
    except Exception:
        db_connected = False

    # Check storage accessibility
    storage_accessible = settings.UPLOADS_DIR.exists() and settings.ANNOTATED_DIR.exists()

    status_info = detection_engine.get_status()

    return SystemHealthResponse(
        status="HEALTHY" if db_connected and storage_accessible else "DEGRADED",
        version=settings.VERSION,
        database_connected=db_connected,
        storage_accessible=storage_accessible,
        model_operational=status_info["is_operational"],
        model_identifier=status_info["model_identifier"],
        model_mode=status_info["mode"],
        active_device=status_info["device"],
        supported_classes=status_info["supported_classes"],
        confidence_threshold=status_info["confidence_threshold"],
        weights_path=status_info["weights_path"],
        weights_exist=status_info["weights_found"],
        total_inspections_stored=total_inspections
    )

@router.post("/model/reload", response_model=ModelReloadResponse)
def reload_model_configuration(payload: ModelReloadRequest):
    """
    Dynamically loads or reconfigures YOLO model weights or confidence thresholds.
    """
    try:
        detection_engine.reload(
            weights_path=payload.weights_path,
            conf=payload.confidence_threshold,
            iou=payload.iou_threshold
        )
        status = detection_engine.get_status()
        return ModelReloadResponse(
            success=True,
            message=f"Model reloaded successfully. Mode: {status['mode']}",
            model_identifier=status["model_identifier"],
            model_mode=status["mode"],
            supported_classes=status["supported_classes"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reload model: {str(e)}")
