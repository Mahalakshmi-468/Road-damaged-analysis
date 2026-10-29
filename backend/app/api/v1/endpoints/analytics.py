from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database.session import get_db
from app.models.inspection import Inspection
from app.models.detection import Detection
from app.schemas.analytics import (
    DashboardAnalyticsResponse,
    MetricSummary,
    TrendPoint,
    CategoryBreakdown,
    SeverityBreakdown,
    ConfidenceDistributionBucket,
    ModelHealthSummary
)
from app.services.detector import detection_engine

router = APIRouter()

@router.get("/dashboard", response_model=DashboardAnalyticsResponse)
def get_dashboard_analytics(db: Session = Depends(get_db)):
    """
    Computes real-time executive dashboard intelligence strictly derived from database records.
    Never fabricates metrics.
    """
    inspections = db.query(Inspection).all()
    detections = db.query(Detection).all()

    total_inspections = len(inspections)
    total_damages = len(detections)

    high_sev = 0
    med_sev = 0
    low_sev = 0
    unk_sev = 0
    pending_ver = 0
    verified = 0
    needs_re = 0
    geotagged = 0

    date_trend_map: Dict[str, Dict[str, int]] = defaultdict(lambda: {"inspections": 0, "damages": 0})

    for ins in inspections:
        eff_sev = ins.effective_severity
        if eff_sev == "HIGH":
            high_sev += 1
        elif eff_sev == "MEDIUM":
            med_sev += 1
        elif eff_sev == "LOW":
            low_sev += 1
        else:
            unk_sev += 1

        if ins.status == "PENDING":
            pending_ver += 1
        elif ins.status == "REVIEWED":
            verified += 1
        elif ins.status == "NEEDS_REINSPECTION":
            needs_re += 1

        if ins.latitude is not None and ins.longitude is not None:
            geotagged += 1

        date_key = ins.created_at.strftime("%Y-%m-%d")
        date_trend_map[date_key]["inspections"] += 1
        date_trend_map[date_key]["damages"] += ins.damage_count

    # Trends sorted chronologically
    sorted_dates = sorted(date_trend_map.keys())
    trends: List[TrendPoint] = [
        TrendPoint(
            date=d,
            inspections=date_trend_map[d]["inspections"],
            damages=date_trend_map[d]["damages"]
        ) for d in sorted_dates
    ]

    # Category Breakdown
    cat_counts: Dict[str, int] = defaultdict(int)
    conf_buckets = {
        "0.10 - 0.30": 0,
        "0.30 - 0.50": 0,
        "0.50 - 0.70": 0,
        "0.70 - 0.85": 0,
        "0.85 - 1.00": 0
    }

    for det in detections:
        cat_counts[det.class_name] += 1
        c = det.confidence
        if c < 0.30:
            conf_buckets["0.10 - 0.30"] += 1
        elif c < 0.50:
            conf_buckets["0.30 - 0.50"] += 1
        elif c < 0.70:
            conf_buckets["0.50 - 0.70"] += 1
        elif c < 0.85:
            conf_buckets["0.70 - 0.85"] += 1
        else:
            conf_buckets["0.85 - 1.00"] += 1

    category_distribution = [
        CategoryBreakdown(
            category=cat,
            count=count,
            percentage=round((count / total_damages) * 100.0, 1) if total_damages > 0 else 0.0
        ) for cat, count in sorted(cat_counts.items(), key=lambda x: x[1], reverse=True)
    ]

    # Severity distribution
    severity_distribution = [
        SeverityBreakdown(
            severity="HIGH",
            count=high_sev,
            percentage=round((high_sev / total_inspections) * 100.0, 1) if total_inspections > 0 else 0.0
        ),
        SeverityBreakdown(
            severity="MEDIUM",
            count=med_sev,
            percentage=round((med_sev / total_inspections) * 100.0, 1) if total_inspections > 0 else 0.0
        ),
        SeverityBreakdown(
            severity="LOW",
            count=low_sev,
            percentage=round((low_sev / total_inspections) * 100.0, 1) if total_inspections > 0 else 0.0
        ),
        SeverityBreakdown(
            severity="UNKNOWN",
            count=unk_sev,
            percentage=round((unk_sev / total_inspections) * 100.0, 1) if total_inspections > 0 else 0.0
        ),
    ]

    confidence_distribution = [
        ConfidenceDistributionBucket(range=k, count=v) for k, v in conf_buckets.items()
    ]

    model_status = detection_engine.get_status()
    model_health = ModelHealthSummary(
        model_identifier=model_status["model_identifier"],
        model_mode=model_status["mode"],
        is_operational=model_status["is_operational"],
        device=model_status["device"],
        active_weights_path=model_status["weights_path"],
        weights_found=model_status["weights_found"],
        supported_classes=model_status["supported_classes"],
        current_confidence_threshold=model_status["confidence_threshold"]
    )

    metrics = MetricSummary(
        total_inspections=total_inspections,
        total_damages_detected=total_damages,
        high_severity_count=high_sev,
        medium_severity_count=med_sev,
        low_severity_count=low_sev,
        unknown_severity_count=unk_sev,
        pending_verification_count=pending_ver,
        verified_count=verified,
        needs_reinspection_count=needs_re,
        geotagged_inspections_count=geotagged
    )

    return DashboardAnalyticsResponse(
        metrics=metrics,
        trends=trends,
        severity_distribution=severity_distribution,
        category_distribution=category_distribution,
        confidence_distribution=confidence_distribution,
        model_health=model_health
    )
