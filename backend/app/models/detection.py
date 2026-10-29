import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.database.session import Base

class Detection(Base):
    __tablename__ = "detections"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    inspection_id = Column(String(36), ForeignKey("inspections.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Classification & Metrics
    class_name = Column(String(64), nullable=False, index=True)
    confidence = Column(Float, nullable=False)
    
    # Bounding Box Coordinates (normalized 0.0 - 1.0)
    x_min = Column(Float, nullable=False)
    y_min = Column(Float, nullable=False)
    x_max = Column(Float, nullable=False)
    y_max = Column(Float, nullable=False)
    
    # Surface Distress Impact
    area_ratio = Column(Float, nullable=False, default=0.0)  # Ratio of bounding box area to total image area
    is_verified = Column(Boolean, nullable=False, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    inspection = relationship("Inspection", back_populates="detections")
