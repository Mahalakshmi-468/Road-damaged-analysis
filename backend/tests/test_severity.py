import pytest
from app.services.severity import calculate_severity_assessment

def test_empty_detections():
    severity, rationale = calculate_severity_assessment([])
    assert severity == "UNKNOWN"
    assert "No distinct road damage" in rationale

def test_single_minor_crack_low_severity():
    detections = [
        {
            "class_name": "Transverse Crack",
            "confidence": 0.55,
            "area_ratio": 0.005
        }
    ]
    severity, rationale = calculate_severity_assessment(detections)
    assert severity in ["LOW", "MEDIUM"]
    assert "Assessed as" in rationale

def test_multiple_potholes_high_severity():
    detections = [
        {
            "class_name": "Pothole",
            "confidence": 0.92,
            "area_ratio": 0.04
        },
        {
            "class_name": "Pothole",
            "confidence": 0.88,
            "area_ratio": 0.03
        }
    ]
    severity, rationale = calculate_severity_assessment(detections)
    assert severity == "HIGH"
    assert "Pothole" in rationale
