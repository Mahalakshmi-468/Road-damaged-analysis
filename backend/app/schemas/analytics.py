from typing import List, Dict
from pydantic import BaseModel

class MetricSummary(BaseModel):
    total_inspections: int
    total_damages_detected: int
    high_severity_count: int
    medium_severity_count: int
    low_severity_count: int
    unknown_severity_count: int
    pending_verification_count: int
    verified_count: int
    needs_reinspection_count: int
    geotagged_inspections_count: int

class TrendPoint(BaseModel):
    date: str
    inspections: int
    damages: int

class CategoryBreakdown(BaseModel):
    category: str
    count: int
    percentage: float

class SeverityBreakdown(BaseModel):
    severity: str
    count: int
    percentage: float

class ConfidenceDistributionBucket(BaseModel):
    range: str
    count: int

class ModelHealthSummary(BaseModel):
    model_identifier: str
    model_mode: str  # "DEEP_LEARNING_YOLO" or "COMPUTER_VISION_ENGINE"
    is_operational: bool
    device: str
    active_weights_path: str
    weights_found: bool
    supported_classes: List[str]
    current_confidence_threshold: float

class DashboardAnalyticsResponse(BaseModel):
    metrics: MetricSummary
    trends: List[TrendPoint]
    severity_distribution: List[SeverityBreakdown]
    category_distribution: List[CategoryBreakdown]
    confidence_distribution: List[ConfidenceDistributionBucket]
    model_health: ModelHealthSummary
