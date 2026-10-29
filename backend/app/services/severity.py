from typing import List, Dict, Tuple, Any

# Structural impact weights according to pavement distress engineering guidelines
CLASS_SEVERITY_WEIGHTS: Dict[str, float] = {
    "Pothole": 1.5,
    "Alligator Crack": 1.4,
    "Rutting": 1.2,
    "Longitudinal Crack": 1.0,
    "Transverse Crack": 0.85,
    "Surface Distress": 0.70,
}

DEFAULT_WEIGHT = 0.80

def calculate_severity_assessment(detections: List[Dict[str, Any]]) -> Tuple[str, str]:
    """
    Computes an engineering-based severity estimate using transparent pavement distress heuristics:
    1. Damage multiplicity (number of defects)
    2. Defect category structural weights (potholes & base fatigue cracks have highest impact)
    3. Aggregate road surface area ratio affected
    4. Maximum defect confidence

    Returns:
        (severity_label, rationale_text)
        severity_label: "LOW" | "MEDIUM" | "HIGH" | "UNKNOWN"
    """
    if not detections:
        return "UNKNOWN", "No distinct road damage instances detected. Surface condition is unclassified or nominal."

    total_area_ratio = sum(d.get("area_ratio", 0.0) for d in detections)
    max_confidence = max(d.get("confidence", 0.0) for d in detections)
    damage_count = len(detections)

    # Calculate weighted impact sum
    weighted_impact = 0.0
    category_counts: Dict[str, int] = {}

    for d in detections:
        cls_name = d.get("class_name", "Surface Distress")
        category_counts[cls_name] = category_counts.get(cls_name, 0) + 1
        w = CLASS_SEVERITY_WEIGHTS.get(cls_name, DEFAULT_WEIGHT)
        
        # Bounding box area contribution (scaled)
        area = d.get("area_ratio", 0.01)
        conf = d.get("confidence", 0.5)
        
        # Area contribution (a 5% surface pothole is massive)
        area_factor = min(area * 100.0 * 2.0, 40.0)
        weighted_impact += (w * 10.0 + area_factor) * conf

    # Multiplicity bonus for multiple defects compounding hazards
    if damage_count > 1:
        weighted_impact *= (1.0 + min((damage_count - 1) * 0.15, 0.6))

    # Determine Severity Tier
    if weighted_impact >= 40.0 or (category_counts.get("Pothole", 0) >= 2) or (category_counts.get("Pothole", 0) >= 1 and total_area_ratio > 0.03):
        severity = "HIGH"
    elif weighted_impact >= 16.0 or damage_count >= 2 or total_area_ratio > 0.015:
        severity = "MEDIUM"
    else:
        severity = "LOW"

    # Generate transparent rationale
    top_categories = [f"{count}x {cat}" for cat, count in category_counts.items()]
    categories_str = ", ".join(top_categories)
    area_pct = total_area_ratio * 100.0

    rationale = (
        f"Assessed as {severity} (Distress Index: {weighted_impact:.1f}/100) based on {damage_count} defect(s): "
        f"[{categories_str}] occupying ~{area_pct:.2f}% of visible road surface with max AI confidence of {max_confidence*100:.1f}%. "
        f"(Note: Rule-based engineering estimate for maintenance prioritization; not a certified prediction of accident probability)."
    )

    return severity, rationale
