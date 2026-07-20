import pytest
from fastapi.testclient import TestClient
from PIL import Image
import io

from app.main import app
from app.services.ingestor import ImageIngestorService

client = TestClient(app)

def generate_test_image_bytes(color=(255, 0, 0), size=(300, 300)) -> bytes:
    img = Image.new("RGB", size, color=color)
    byte_arr = io.BytesIO()
    img.save(byte_arr, format='PNG')
    return byte_arr.getvalue()

def test_health_check():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_root_route():
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "SourcingPlus" in response.text

def test_sync_catalog_empty():
    payload = {"products": []}
    response = client.post("/api/v1/sync", json=payload)
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["status"] == "success"
    assert res_data["processed_count"] == 0
    assert res_data["indexed_count"] == 0

def test_sync_catalog_success(monkeypatch):
    # Mock download_image to avoid outgoing HTTP request
    mock_bytes = generate_test_image_bytes()
    
    async def mock_download(*args, **kwargs):
        return mock_bytes
        
    monkeypatch.setattr(ImageIngestorService, "download_image", mock_download)
    
    payload = {
        "products": [
            {
                "id": "prod-api-1",
                "sku": "SKU-API-1",
                "price": 99.99,
                "category": "Shoes",
                "inventory": 15,
                "image_url": "https://picsum.photos/200"
            }
        ]
    }
    
    response = client.post("/api/v1/sync", json=payload)
    assert response.status_code == 200
    res_data = response.json()
    
    assert res_data["status"] == "success"
    assert res_data["processed_count"] == 1
    assert res_data["indexed_count"] == 1
    assert len(res_data["errors"]) == 0
