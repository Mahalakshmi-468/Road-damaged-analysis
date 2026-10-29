import io
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_full_inspection_lifecycle():
    sample_path = Path(__file__).resolve().parent.parent.parent / "sample_images" / "pothole_sample_1.jpg"
    assert sample_path.exists(), f"Sample image not found at {sample_path}"

    with open(sample_path, "rb") as f:
        file_bytes = f.read()

    # 1. Upload and detect
    response = client.post(
        "/api/v1/inspections/upload-and-detect",
        files={"file": ("pothole_sample_1.jpg", file_bytes, "image/jpeg")},
        data={
            "title": "Highway NH44 Pothole Test",
            "latitude": 13.0827,
            "longitude": 80.2707,
            "location_name": "NH44 Outer Ring Road, Sector 4",
            "confidence_threshold": 0.20
        }
    )
    assert response.status_code == 200, response.text
    data = response.json()
    inspection_id = data["id"]
    assert data["title"] == "Highway NH44 Pothole Test"
    assert data["latitude"] == 13.0827
    assert data["location_source"] == "MANUAL"
    assert data["effective_severity"] in ["LOW", "MEDIUM", "HIGH", "UNKNOWN"]
    assert "image_url" in data
    assert "annotated_image_url" in data

    # 2. Get detail
    get_res = client.get(f"/api/v1/inspections/{inspection_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == inspection_id

    # 3. Patch review
    patch_res = client.patch(
        f"/api/v1/inspections/{inspection_id}",
        json={
            "status": "REVIEWED",
            "manual_severity": "HIGH",
            "reviewer_notes": "Confirmed active severe pothole hazard. Scheduled for cold mix patching."
        }
    )
    assert patch_res.status_code == 200
    patch_data = patch_res.json()
    assert patch_data["status"] == "REVIEWED"
    assert patch_data["manual_severity"] == "HIGH"
    assert patch_data["effective_severity"] == "HIGH"

    # 4. Export PDF
    pdf_res = client.get(f"/api/v1/reports/inspections/{inspection_id}/pdf")
    assert pdf_res.status_code == 200
    assert pdf_res.headers["content-type"] == "application/pdf"
    assert len(pdf_res.content) > 1000

    # 5. Export CSV
    csv_res = client.get("/api/v1/reports/export/csv")
    assert csv_res.status_code == 200
    assert "Inspection ID" in csv_res.text

    # 6. Dashboard analytics check
    dash_res = client.get("/api/v1/analytics/dashboard")
    assert dash_res.status_code == 200
    dash_data = dash_res.json()
    assert dash_data["metrics"]["total_inspections"] >= 1
    assert dash_data["model_health"]["is_operational"] is True
