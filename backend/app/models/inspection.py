import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, DateTime, Text
from sqlalchemy.orm import relationship
from app.database.session import Base

class Inspection(Base):
    __tablename__ = "inspections"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    title = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    image_path = Column(String(512), nullable=False)
    annotated_image_path = Column(String(512), nullable=False)
    image_width = Column(Integer, nullable=False, default=0)
    image_height = Column(Integer, nullable=False, default=0)
    file_size_bytes = Column(Integer, nullable=False, default=0)
    mime_type = Column(String(64), nullable=False, default="image/jpeg")

    # Geospatial data
    latitude = Column(Float, nullable=True, index=True)
    longitude = Column(Float, nullable=True, index=True)
    location_name = Column(String(255), nullable=True)
    location_source = Column(String(32), nullable=False, default="NONE")  # GPS_EXIF, MANUAL, NONE

    # Severity Assessment
    ai_severity = Column(String(32), nullable=False, default="UNKNOWN")  # LOW, MEDIUM, HIGH, UNKNOWN
    manual_severity = Column(String(32), nullable=True)  # Human override
    severity_rationale = Column(Text, nullable=True)     # Explanation of rule-based calculation

    # Human Review & Lifecycle
    status = Column(String(32), nullable=False, default="PENDING", index=True)  # PENDING, REVIEWED, NEEDS_REINSPECTION
    reviewer_notes = Column(Text, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)

    # AI Model Execution Metadata
    model_identifier = Column(String(128), nullable=False)
    inference_ms = Column(Float, nullable=False, default=0.0)
    damage_count = Column(Integer, nullable=False, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    detections = relationship("Detection", back_populates="inspection", cascade="all, delete-orphan", order_by="desc(Detection.confidence)")

    @property
    def effective_severity(self) -> str:
        """Returns human-verified severity if set; otherwise falls back to AI estimated severity."""
        return self.manual_severity if self.manual_severity else self.ai_severity
