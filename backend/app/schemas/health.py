from typing import List, Optional
from pydantic import BaseModel

class SystemHealthResponse(BaseModel):
    status: str
    version: str
    database_connected: bool
    storage_accessible: bool
    model_operational: bool
    model_identifier: str
    model_mode: str
    active_device: str
    supported_classes: List[str]
    confidence_threshold: float
    weights_path: str
    weights_exist: bool
    total_inspections_stored: int

class ModelReloadRequest(BaseModel):
    weights_path: Optional[str] = None
    confidence_threshold: Optional[float] = None
    iou_threshold: Optional[float] = None

class ModelReloadResponse(BaseModel):
    success: bool
    message: str
    model_identifier: str
    model_mode: str
    supported_classes: List[str]
