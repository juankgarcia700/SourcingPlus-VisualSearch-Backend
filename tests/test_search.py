import pytest
from fastapi.testclient import TestClient
from PIL import Image
import io

from app.main import app
from app.services.vectorizer import get_pinecone_index, upsert_products_to_pinecone, generate_embedding
from app.services.cache import query_cache
from app.services.ingestor import ImageIngestorService

client = TestClient(app)

def generate_test_image_bytes(color=(255, 0, 0), size=(224, 224)) -> bytes:
    img = Image.new("RGB", size, color=color)
    byte_arr = io.BytesIO()
    img.save(byte_arr, format='PNG')
    return byte_arr.getvalue()

@pytest.fixture(autouse=True)
def setup_test_index():
    # Clear index vectors and cache before each test
    index = get_pinecone_index()
    if hasattr(index, "_vectors"):
        index._vectors.clear()
    query_cache.clear()
    
    # Seed 3 mock products:
    # 1. Red Shirt - In Stock (10)
    # 2. Green Pants - Out of Stock (0)
    # 3. Red Shoes - In Stock (5)
    img_red = Image.new("RGB", (224, 224), color=(255, 0, 0))
    img_green = Image.new("RGB", (224, 224), color=(0, 255, 0))
    
    products = [
        {"id": "red-shirt", "image": img_red, "sku": "SH-RED-1", "price": 25.0, "category": "Shirts", "inventory": 10},
        {"id": "green-pants", "image": img_green, "sku": "PA-GRN-1", "price": 40.0, "category": "Pants", "inventory": 0},
        {"id": "red-shoes", "image": img_red, "sku": "SH-RED-2", "price": 60.0, "category": "Shoes", "inventory": 5}
    ]
    upsert_products_to_pinecone(products)

def test_search_by_url_caching(monkeypatch):
    # Mock download_image to return red image bytes
    mock_bytes = generate_test_image_bytes(color=(255, 0, 0))
    async def mock_download(*args, **kwargs):
        return mock_bytes
    monkeypatch.setattr(ImageIngestorService, "download_image", mock_download)

    payload = {
        "image_url": "https://picsum.photos/red-img.png",
        "top_k": 5,
        "score_threshold": 0.0,
        "in_stock_only": False,
        "category": None
    }
    
    # First search: Cache Miss
    res1 = client.post("/api/v1/search/url", json=payload)
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["cache_hit"] is False
    assert len(data1["results"]) >= 2
    
    # Second search: Cache Hit
    res2 = client.post("/api/v1/search/url", json=payload)
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["cache_hit"] is True
    assert len(data2["results"]) == len(data1["results"])

def test_search_in_stock_only(monkeypatch):
    # Query with green image bytes (out of stock pants)
    mock_bytes = generate_test_image_bytes(color=(0, 255, 0))
    async def mock_download(*args, **kwargs):
        return mock_bytes
    monkeypatch.setattr(ImageIngestorService, "download_image", mock_download)
    
    # 1. Search with in_stock_only = False (should return green pants)
    payload_all = {
        "image_url": "https://picsum.photos/green.png",
        "in_stock_only": False
    }
    res_all = client.post("/api/v1/search/url", json=payload_all)
    data_all = res_all.json()
    matches_all = [item["id"] for item in data_all["results"]]
    assert "green-pants" in matches_all

    # 2. Search with in_stock_only = True (should NOT return green pants since inventory = 0)
    payload_stock = {
        "image_url": "https://picsum.photos/green.png",
        "in_stock_only": True
    }
    res_stock = client.post("/api/v1/search/url", json=payload_stock)
    data_stock = res_stock.json()
    matches_stock = [item["id"] for item in data_stock["results"]]
    assert "green-pants" not in matches_stock

def test_search_category_filter(monkeypatch):
    # Query with red image (matches red-shirt and red-shoes)
    mock_bytes = generate_test_image_bytes(color=(255, 0, 0))
    async def mock_download(*args, **kwargs):
        return mock_bytes
    monkeypatch.setattr(ImageIngestorService, "download_image", mock_download)

    # Filter to category "Shoes" only
    payload = {
        "image_url": "https://picsum.photos/red.png",
        "category": "Shoes"
    }
    res = client.post("/api/v1/search/url", json=payload)
    data = res.json()
    for item in data["results"]:
        assert item["category"] == "Shoes"
        assert item["id"] == "red-shoes"

def test_search_score_threshold(monkeypatch):
    # Query with red image (matches red-shirt with high score 1.0, green-pants with low score)
    mock_bytes = generate_test_image_bytes(color=(255, 0, 0))
    async def mock_download(*args, **kwargs):
        return mock_bytes
    monkeypatch.setattr(ImageIngestorService, "download_image", mock_download)

    payload = {
        "image_url": "https://picsum.photos/red.png",
        "score_threshold": 0.9  # Set high threshold
    }
    res = client.post("/api/v1/search/url", json=payload)
    data = res.json()
    for item in data["results"]:
        assert item["score"] >= 0.9

def test_search_by_file_caching():
    img_bytes = generate_test_image_bytes(color=(255, 0, 0))
    file_payload = {"file": ("red_query.png", img_bytes, "image/png")}
    
    # First search: Cache Miss
    res1 = client.post("/api/v1/search/file", files=file_payload)
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["cache_hit"] is False
    
    # Second search with same image bytes: Cache Hit
    res2 = client.post("/api/v1/search/file", files={"file": ("red_query.png", img_bytes, "image/png")})
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["cache_hit"] is True
