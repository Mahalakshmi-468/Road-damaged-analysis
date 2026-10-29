import os
import time
import cv2
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from app.core.config import settings
from app.core.logging import logger

# Standard Road Distress Taxonomy
ROAD_DISTRESS_CLASSES = [
    "Pothole",
    "Longitudinal Crack",
    "Transverse Crack",
    "Alligator Crack",
    "Rutting",
    "Surface Distress"
]

# RDD dataset code mappings
RDD_CODE_MAP = {
    "D00": "Longitudinal Crack",
    "D10": "Transverse Crack",
    "D20": "Alligator Crack",
    "D40": "Pothole",
    "D01": "Longitudinal Crack",
    "D11": "Transverse Crack",
    "pothole": "Pothole",
    "crack": "Longitudinal Crack",
    "alligator_crack": "Alligator Crack",
    "transverse_crack": "Transverse Crack",
    "rutting": "Rutting"
}

class DetectionEngine:
    """
    Enterprise-grade dual-mode AI road distress detection engine.
    - Mode A: Ultralytics YOLO with road-damage-trained weights (.pt / .onnx)
    - Mode B: RoadGuard Computer Vision Distress Engine (Deterministic OpenCV edge, contour, and morphological analysis)
    """

    def __init__(self):
        self.weights_path: str = settings.MODEL_WEIGHTS_PATH
        self.confidence_threshold: float = settings.DEFAULT_CONFIDENCE_THRESHOLD
        self.iou_threshold: float = settings.DEFAULT_IOU_THRESHOLD
        self.yolo_model = None
        self.mode: str = "COMPUTER_VISION_ENGINE"
        self.device: str = "CPU"
        self.model_identifier: str = "RoadGuard-CV-Distress-Analyzer-v1.2"
        self.supported_classes: List[str] = ROAD_DISTRESS_CLASSES
        self.weights_found: bool = False

        self._load_engine()

    def _load_engine(self):
        """Attempts to load YOLO weights if present and valid for road damage."""
        weights_file = Path(self.weights_path)
        if weights_file.exists() and weights_file.is_file():
            try:
                from ultralytics import YOLO
                import torch
                self.device = "CUDA" if torch.cuda.is_available() else "CPU"
                logger.info(f"Loading YOLO weights from: {weights_file.resolve()} on {self.device}")
                model = YOLO(str(weights_file.resolve()))

                # Inspect model classes
                model_classes = model.names if hasattr(model, "names") else {}
                class_names_lower = [str(v).lower() for v in model_classes.values()]

                # Verify if weights actually detect road damage or just standard COCO objects
                has_road_classes = any(
                    any(rdd_term in cls_name for rdd_term in ["d00", "d10", "d20", "d40", "pothole", "crack", "rutting"])
                    for cls_name in class_names_lower
                )

                if has_road_classes:
                    self.yolo_model = model
                    self.mode = "DEEP_LEARNING_YOLO"
                    self.weights_found = True
                    self.model_identifier = f"YOLOv8-RDD ({weights_file.name})"
                    self.supported_classes = [
                        RDD_CODE_MAP.get(name, name) for name in model_classes.values()
                    ]
                    logger.info(f"Loaded road-damage deep learning model with {len(self.supported_classes)} classes.")
                    return
                else:
                    logger.warning(
                        f"Model at {weights_file} does not contain specialized road damage classes "
                        f"(Found generic classes: {list(model_classes.values())[:5]}...). "
                        f"Per guidelines, falling back to RoadGuard Computer Vision Distress Engine "
                        f"to prevent false predictions."
                    )
            except Exception as e:
                logger.error(f"Failed to load YOLO model from {weights_file}: {e}")

        # Fallback to RoadGuard Computer Vision Distress Engine
        self.yolo_model = None
        self.mode = "COMPUTER_VISION_ENGINE"
        self.weights_found = False
        self.model_identifier = "RoadGuard-CV-Distress-Analyzer-v1.2"
        self.supported_classes = ROAD_DISTRESS_CLASSES
        logger.info("Active engine: RoadGuard Computer Vision Distress Analyzer (Deterministic OpenCV Pavement Defect Analysis).")

    def reload(self, weights_path: Optional[str] = None, conf: Optional[float] = None, iou: Optional[float] = None):
        """Allows hot-reloading weights or adjusting detection parameters at runtime."""
        if weights_path:
            self.weights_path = weights_path
        if conf is not None:
            self.confidence_threshold = max(0.05, min(0.95, conf))
        if iou is not None:
            self.iou_threshold = max(0.1, min(0.95, iou))
        self._load_engine()

    def get_status(self) -> Dict[str, Any]:
        return {
            "mode": self.mode,
            "model_identifier": self.model_identifier,
            "device": self.device,
            "weights_path": self.weights_path,
            "weights_found": self.weights_found,
            "supported_classes": self.supported_classes,
            "confidence_threshold": self.confidence_threshold,
            "iou_threshold": self.iou_threshold,
            "is_operational": True
        }

    def detect(self, image_bgr: np.ndarray, conf_override: Optional[float] = None) -> Tuple[List[Dict[str, Any]], float]:
        """
        Runs real detection on an image (OpenCV BGR ndarray).
        Returns:
            (detections_list, inference_duration_ms)
        """
        start_time = time.perf_counter()
        conf = conf_override if conf_override is not None else self.confidence_threshold

        if self.mode == "DEEP_LEARNING_YOLO" and self.yolo_model is not None:
            detections = self._run_yolo_inference(image_bgr, conf)
        else:
            detections = self._run_cv_inference(image_bgr, conf)

        inference_ms = (time.perf_counter() - start_time) * 1000.0
        return detections, round(inference_ms, 2)

    def _run_yolo_inference(self, image_bgr: np.ndarray, conf: float) -> List[Dict[str, Any]]:
        """Executes inference using loaded Ultralytics YOLO model."""
        h, w = image_bgr.shape[:2]
        total_pixels = float(h * w)
        results = self.yolo_model.predict(
            source=image_bgr,
            conf=conf,
            iou=self.iou_threshold,
            verbose=False,
            device=self.device.lower()
        )

        detections = []
        if results and len(results) > 0:
            boxes = results[0].boxes
            for box in boxes:
                xyxy = box.xyxy[0].tolist()  # [x1, y1, x2, y2]
                score = float(box.conf[0])
                cls_idx = int(box.cls[0])
                raw_name = results[0].names.get(cls_idx, "Damage")
                clean_name = RDD_CODE_MAP.get(raw_name, raw_name)

                x1, y1, x2, y2 = xyxy
                # Normalize 0.0 - 1.0
                norm_x1 = max(0.0, min(1.0, x1 / w))
                norm_y1 = max(0.0, min(1.0, y1 / h))
                norm_x2 = max(0.0, min(1.0, x2 / w))
                norm_y2 = max(0.0, min(1.0, y2 / h))

                box_area = max(0.0, (x2 - x1) * (y2 - y1))
                area_ratio = min(1.0, box_area / total_pixels)

                detections.append({
                    "class_name": clean_name,
                    "confidence": round(score, 3),
                    "x_min": round(norm_x1, 4),
                    "y_min": round(norm_y1, 4),
                    "x_max": round(norm_x2, 4),
                    "y_max": round(norm_y2, 4),
                    "area_ratio": round(area_ratio, 5),
                    "is_verified": True
                })

        return detections

    def _run_cv_inference(self, image_bgr: np.ndarray, conf_threshold: float) -> List[Dict[str, Any]]:
        """
        Executes real computer vision road distress analysis using OpenCV:
        1. Grayscale & adaptive preprocessing
        2. Bilateral filtering to preserve distress boundaries while smoothing asphalt grain
        3. Canny edge detection & Morphological gradient closures
        4. Contour extraction & geometric feature classification:
           - Potholes: Low aspect ratio (elliptical/round), dark cavity contrast relative to ambient road.
           - Longitudinal Cracks: Vertical elongated distress patterns.
           - Transverse Cracks: Horizontal elongated distress patterns across lanes.
           - Alligator Cracks: High edge density, multi-junction network.
        5. Computes real bounding boxes and normalized coordinates.
        """
        h, w = image_bgr.shape[:2]
        total_pixels = float(h * w)

        gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
        
        # Suppress noise while keeping crack/pothole edges sharp
        filtered = cv2.bilateralFilter(gray, d=7, sigmaColor=50, sigmaSpace=50)

        # Compute adaptive threshold and edges
        mean_brightness = float(np.mean(gray))
        lower_thresh = max(20, int(mean_brightness * 0.45))
        upper_thresh = max(60, int(mean_brightness * 0.90))
        edges = cv2.Canny(filtered, lower_thresh, upper_thresh)

        # Morphological closing to bridge fragmented crack lines and consolidate cavity blobs
        kernel_cross = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        closed_edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel_cross)

        # Invert intensity for dark defect / cavity detection
        dark_pothole_mask = cv2.inRange(gray, 0, max(30, int(mean_brightness * 0.65)))
        combined_distress = cv2.bitwise_or(closed_edges, dark_pothole_mask)

        # Find contours of distress instances
        contours, _ = cv2.findContours(combined_distress, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        detections = []
        # Filter out minor asphalt pebbles and extreme edge artifacts
        min_defect_area = max(400, int(total_pixels * 0.0008))
        max_defect_area = int(total_pixels * 0.40)

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < min_defect_area or area > max_defect_area:
                continue

            x, y, bw, bh = cv2.boundingRect(cnt)
            # Avoid full-border artifacts
            if bw >= w * 0.98 or bh >= h * 0.98:
                continue

            aspect_ratio = float(bw) / float(bh) if bh > 0 else 1.0
            box_area = float(bw * bh)
            area_ratio = box_area / total_pixels
            extent = area / box_area if box_area > 0 else 0.0

            # Inspect region inside the defect
            roi_gray = gray[y:y+bh, x:x+bw]
            roi_mean = float(np.mean(roi_gray)) if roi_gray.size > 0 else mean_brightness
            contrast_diff = (mean_brightness - roi_mean) / max(1.0, mean_brightness)

            # Classify distress type geometrically
            if contrast_diff > 0.18 and 0.45 <= aspect_ratio <= 2.2 and extent > 0.35:
                # Darker depression cavity with roughly circular/oval shape -> Pothole
                cls_name = "Pothole"
                base_conf = 0.65 + min(0.30, contrast_diff * 0.6 + extent * 0.1)
            elif aspect_ratio < 0.45 and bh > 50:
                # Strongly vertical elongated continuous crack -> Longitudinal Crack
                cls_name = "Longitudinal Crack"
                base_conf = 0.60 + min(0.32, (1.0 / max(0.1, aspect_ratio)) * 0.05)
            elif aspect_ratio > 2.2 and bw > 60:
                # Strongly horizontal elongated crack across road -> Transverse Crack
                cls_name = "Transverse Crack"
                base_conf = 0.60 + min(0.32, (aspect_ratio * 0.04))
            elif area > min_defect_area * 2.5 and extent < 0.40:
                # High perimeter, branched mesh geometry -> Alligator Crack
                cls_name = "Alligator Crack"
                base_conf = 0.58 + min(0.30, (area / (min_defect_area * 5)) * 0.1)
            else:
                cls_name = "Surface Distress"
                base_conf = 0.52 + min(0.25, contrast_diff * 0.4)

            # Cap confidence within valid range
            conf_val = round(max(0.10, min(0.96, base_conf)), 3)

            # Apply user-specified confidence filter
            if conf_val < conf_threshold:
                continue

            norm_x1 = max(0.0, min(1.0, x / w))
            norm_y1 = max(0.0, min(1.0, y / h))
            norm_x2 = max(0.0, min(1.0, (x + bw) / w))
            norm_y2 = max(0.0, min(1.0, (y + bh) / h))

            detections.append({
                "class_name": cls_name,
                "confidence": conf_val,
                "x_min": round(norm_x1, 4),
                "y_min": round(norm_y1, 4),
                "x_max": round(norm_x2, 4),
                "y_max": round(norm_y2, 4),
                "area_ratio": round(area_ratio, 5),
                "is_verified": True
            })

        # Non-maximum suppression / overlapping box suppression
        detections = self._suppress_overlapping_boxes(detections, iou_thresh=0.40)
        return detections

    def _suppress_overlapping_boxes(self, detections: List[Dict[str, Any]], iou_thresh: float) -> List[Dict[str, Any]]:
        """Filters out heavily overlapping bounding boxes, preserving higher confidence."""
        if len(detections) <= 1:
            return detections

        detections.sort(key=lambda d: d["confidence"], reverse=True)
        keep = []

        for d in detections:
            overlap = False
            for kept in keep:
                # Compute IoU
                x1 = max(d["x_min"], kept["x_min"])
                y1 = max(d["y_min"], kept["y_min"])
                x2 = min(d["x_max"], kept["x_max"])
                y2 = min(d["y_max"], kept["y_max"])
                inter_w = max(0.0, x2 - x1)
                inter_h = max(0.0, y2 - y1)
                inter_area = inter_w * inter_h

                area_d = (d["x_max"] - d["x_min"]) * (d["y_max"] - d["y_min"])
                area_k = (kept["x_max"] - kept["x_min"]) * (kept["y_max"] - kept["y_min"])
                union_area = area_d + area_k - inter_area

                iou = inter_area / union_area if union_area > 0 else 0.0
                if iou > iou_thresh:
                    overlap = True
                    break
            if not overlap:
                keep.append(d)

        return keep

# Global singleton instance
detection_engine = DetectionEngine()
