import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "ROADGUARD AI"
    assert data["status"] == "ONLINE"

def test_health_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["database_connected"] is True
    assert data["model_operational"] is True
    assert "model_identifier" in data
    assert len(data["supported_classes"]) > 0
