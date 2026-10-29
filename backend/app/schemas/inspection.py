from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict

class DetectionBase(BaseModel):
    class_name: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    x_min: float = Field(..., ge=0.0, le=1.0)
    y_min: float = Field(..., ge=0.0, le=1.0)
    x_max: float = Field(..., ge=0.0, le=1.0)
    y_max: float = Field(..., ge=0.0, le=1.0)
    area_ratio: float = Field(..., ge=0.0, le=1.0)
    is_verified: bool = True

class DetectionCreate(DetectionBase):
    pass

class DetectionResponse(DetectionBase):
    id: str
    inspection_id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class InspectionReviewUpdate(BaseModel):
    status: Optional[str] = Field(None, description="PENDING, REVIEWED, NEEDS_REINSPECTION")
    manual_severity: Optional[str] = Field(None, description="LOW, MEDIUM, HIGH, UNKNOWN, or null to reset to AI")
    reviewer_notes: Optional[str] = None

class InspectionResponse(BaseModel):
    id: str
    title: str
    original_filename: str
    image_url: str
    annotated_image_url: str
    image_width: int
    image_height: int
    file_size_bytes: int
    mime_type: str
    
    # Geospatial
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    location_name: Optional[str] = None
    location_source: str
    
    # Severity
    ai_severity: str
    manual_severity: Optional[str] = None
    effective_severity: str
    severity_rationale: Optional[str] = None
    
    # Review
    status: str
    reviewer_notes: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    
    # AI Metadata
    model_identifier: str
    inference_ms: float
    damage_count: int
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    
    detections: List[DetectionResponse] = []

    model_config = ConfigDict(from_attributes=True)

class InspectionListResponse(BaseModel):
    total: int
    page: int
    limit: int
    items: List[InspectionResponse]
