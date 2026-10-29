import os
import uuid
import cv2
import numpy as np
from pathlib import Path
from typing import Tuple, List, Dict, Any
from PIL import Image, ImageOps
from fastapi import UploadFile, HTTPException
from app.core.config import settings
from app.core.logging import logger

# BGR color palette for professional inspection bounding boxes
CLASS_COLORS = {
    "Pothole": (38, 38, 239),          # Red / Crimson
    "Alligator Crack": (210, 60, 180),  # Magenta / Violet
    "Longitudinal Crack": (235, 182, 6),# Electric Cyan / Teal
    "Transverse Crack": (30, 165, 250), # Vivid Amber / Orange
    "Rutting": (50, 215, 255),          # Golden Yellow
    "Surface Distress": (180, 180, 40)  # Bright Mint / Lime
}
DEFAULT_BOX_COLOR = (235, 182, 6)

def validate_uploaded_image(file: UploadFile) -> Tuple[bytes, str]:
    """
    Validates file extension, MIME type, size limit, and PIL decodability.
    Returns:
        (file_bytes, safe_extension)
    """
    filename = file.filename or "upload.jpg"
    ext = Path(filename).suffix.lower()

    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format '{ext}'. Allowed extensions are: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )

    # Read bytes and check size
    file_bytes = file.file.read()
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(file_bytes) > max_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB}MB."
        )

    if len(file_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    # Verify image integrity with PIL
    import io
    try:
        with Image.open(io.BytesIO(file_bytes)) as img:
            img.verify()
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Corrupted or invalid image file: {str(e)}"
        )

    # Re-open to read format and dimension
    return file_bytes, ext

def save_original_image(file_bytes: bytes, extension: str) -> Tuple[str, str, int, int]:
    """
    Saves the original uploaded image to storage/uploads with a secure unique ID.
    Returns:
        (relative_storage_path, absolute_path, width, height)
    """
    file_id = str(uuid.uuid4())
    filename = f"{file_id}{extension}"
    dest_path = settings.UPLOADS_DIR / filename

    with open(dest_path, "wb") as f:
        f.write(file_bytes)

    # Read image dimensions
    image_np = cv2.imdecode(np.frombuffer(file_bytes, np.uint8), cv2.IMREAD_COLOR)
    if image_np is None:
        raise HTTPException(status_code=500, detail="Failed to decode image data.")
    
    h, w = image_np.shape[:2]
    relative_path = f"storage/uploads/{filename}"
    return relative_path, str(dest_path), w, h

def render_annotated_image(
    original_path: str,
    detections: List[Dict[str, Any]],
    output_filename: str
) -> Tuple[str, str]:
    """
    Renders high-visibility bounding boxes, confident class tags, and surface severity overlays.
    Saves to storage/annotated/.
    Returns:
        (relative_storage_path, absolute_path)
    """
    image_bgr = cv2.imread(original_path)
    if image_bgr is None:
        raise FileNotFoundError(f"Could not read source image at: {original_path}")

    h, w = image_bgr.shape[:2]
    annotated = image_bgr.copy()

    # Dynamic line thickness based on resolution
    line_thickness = max(2, int(min(w, h) / 400))
    font_scale = max(0.45, min(w, h) / 1000.0)
    font_thickness = max(1, int(line_thickness / 2))

    for det in detections:
        x1 = int(det["x_min"] * w)
        y1 = int(det["y_min"] * h)
        x2 = int(det["x_max"] * w)
        y2 = int(det["y_max"] * h)

        cls_name = det.get("class_name", "Distress")
        conf = det.get("confidence", 0.0)
        color = CLASS_COLORS.get(cls_name, DEFAULT_BOX_COLOR)

        # Draw main bounding box with rounded corner accents
        cv2.rectangle(annotated, (x1, y1), (x2, y2), color, line_thickness, cv2.LINE_AA)

        # Draw corner brackets for high-tech HUD look
        bracket_len = min(20, int((x2 - x1) * 0.25), int((y2 - y1) * 0.25))
        if bracket_len > 4:
            # Top-left
            cv2.line(annotated, (x1, y1), (x1 + bracket_len, y1), (255, 255, 255), line_thickness + 1, cv2.LINE_AA)
            cv2.line(annotated, (x1, y1), (x1, y1 + bracket_len), (255, 255, 255), line_thickness + 1, cv2.LINE_AA)
            # Bottom-right
            cv2.line(annotated, (x2, y2), (x2 - bracket_len, y2), (255, 255, 255), line_thickness + 1, cv2.LINE_AA)
            cv2.line(annotated, (x2, y2), (x2, y2 - bracket_len), (255, 255, 255), line_thickness + 1, cv2.LINE_AA)

        # Prepare label text
        label_text = f"{cls_name} {int(conf * 100)}%"
        (text_w, text_h), baseline = cv2.getTextSize(
            label_text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, font_thickness
        )

        # Label background pill
        label_y1 = max(0, y1 - text_h - 10)
        label_y2 = y1
        label_x1 = x1
        label_x2 = min(w, x1 + text_w + 14)

        # Draw dark semi-transparent banner for readability
        overlay = annotated.copy()
        cv2.rectangle(overlay, (label_x1, label_y1), (label_x2, label_y2), (15, 23, 42), -1)
        cv2.addWeighted(overlay, 0.85, annotated, 0.15, 0, annotated)

        # Accent border on label
        cv2.rectangle(annotated, (label_x1, label_y1), (label_x2, label_y2), color, 1, cv2.LINE_AA)

        # Text in white/bright
        cv2.putText(
            annotated,
            label_text,
            (label_x1 + 6, label_y2 - 5),
            cv2.FONT_HERSHEY_SIMPLEX,
            font_scale,
            (255, 255, 255),
            font_thickness,
            cv2.LINE_AA
        )

    # Save annotated image
    dest_path = settings.ANNOTATED_DIR / output_filename
    cv2.imwrite(str(dest_path), annotated)

    relative_path = f"storage/annotated/{output_filename}"
    return relative_path, str(dest_path)
