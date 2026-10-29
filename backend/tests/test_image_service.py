import pytest
import io
from fastapi import UploadFile, HTTPException
from app.services.image_service import validate_uploaded_image

def test_invalid_extension():
    fake_file = UploadFile(
        filename="road.txt",
        file=io.BytesIO(b"fake text content")
    )
    with pytest.raises(HTTPException) as excinfo:
        validate_uploaded_image(fake_file)
    assert excinfo.value.status_code == 400
    assert "Unsupported file format" in excinfo.value.detail

def test_empty_file():
    fake_file = UploadFile(
        filename="road.jpg",
        file=io.BytesIO(b"")
    )
    with pytest.raises(HTTPException) as excinfo:
        validate_uploaded_image(fake_file)
    assert excinfo.value.status_code == 400
