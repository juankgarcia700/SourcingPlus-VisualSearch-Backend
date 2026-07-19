import pytest
from fastapi.testclient import TestClient
from PIL import Image
import io
import hashlib

from app.main import app
from app.services.vectorizer import get_pinecone_index, upsert_products_to_pinecone
from app.services.cache import query_cache
from app.services.ingestor import ImageIngestorService
from app.database import SessionLocal, Base, engine
from app.models import Product

client = TestClient(app)

def generate_test_image_bytes(color=(0, 0, 255), size=(224, 224)) -> bytes:
    img = Image.new("RGB", size, color=color)
    byte_arr = io.BytesIO()
    img.save(byte_arr, format='PNG')
    return byte_arr.getvalue()

@pytest.fixture(autouse=True)
def setup_hybrid_test_data():
    # Setup clean databases
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        db.query(Product).delete()
        db.commit()
    except Exception:
        db.rollback()

    index = get_pinecone_index()
    if hasattr(index, "_vectors"):
        index._vectors.clear()
    query_cache.clear()

    # Seed products with varying prices and brands:
    # 1. Budget shirt: $15.00, Brand: Acme
    # 2. Medium pants: $55.00, Brand: Acme
    # 3. Premium shoes: $180.00, Brand: Nike
    img_blue = Image.new("RGB", (224, 224), color=(0, 0, 255))
    
    products = [
        {"id": "budget-shirt", "image": img_blue, "sku": "BUD-SH-1", "price": 15.00, "category": "Shirts", "inventory": 10},
        {"id": "medium-pants", "image": img_blue, "sku": "MED-PA-1", "price": 55.00, "category": "Pants", "inventory": 12},
        {"id": "premium-shoes", "image": img_blue, "sku": "PREM-SH-2", "price": 180.00, "category": "Shoes", "inventory": 5}
    ]
    upsert_products_to_pinecone(products)

    # Seed same products to SQL
    db_prods = [
        Product(id="budget-shirt", sku="BUD-SH-1", title="Budget Shirt", price=15.00, category="Shirts", inventory=10, image_url="http://example.com/b.jpg", brand="Acme"),
        Product(id="medium-pants", sku="MED-PA-1", title="Medium Pants", price=55.00, category="Pants", inventory=12, image_url="http://example.com/m.jpg", brand="Acme"),
        Product(id="premium-shoes", sku="PREM-SH-2", title="Premium Shoes", price=180.00, category="Shoes", inventory=5, image_url="http://example.com/p.jpg", brand="Nike")
    ]
    for dp in db_prods:
        db.add(dp)
    db.commit()
    db.close()


def test_price_range_filtering(monkeypatch):
    mock_bytes = generate_test_image_bytes(color=(0, 0, 255))
    async def mock_download(*args, **kwargs):
        return mock_bytes
    monkeypatch.setattr(ImageIngestorService, "download_image", mock_download)

    # 1. Search with max_price = 60.0 (Should return budget-shirt and medium-pants)
    payload_max = {
        "image_url": "https://picsum.photos/blue.png",
        "max_price": 60.0
    }
    res = client.post("/api/v1/search/url", json=payload_max)
    assert res.status_code == 200
    data = res.json()
    ids = [item["id"] for item in data["results"]]
    assert "budget-shirt" in ids
    assert "medium-pants" in ids
    assert "premium-shoes" not in ids

    # 2. Search with min_price = 100.0 (Should only return premium-shoes)
    payload_min = {
        "image_url": "https://picsum.photos/blue.png",
        "min_price": 100.0
    }
    res = client.post("/api/v1/search/url", json=payload_min)
    assert res.status_code == 200
    data = res.json()
    ids = [item["id"] for item in data["results"]]
    assert "premium-shoes" in ids
    assert "budget-shirt" not in ids
    assert "medium-pants" not in ids


def test_brand_filtering(monkeypatch):
    mock_bytes = generate_test_image_bytes(color=(0, 0, 255))
    async def mock_download(*args, **kwargs):
        return mock_bytes
    monkeypatch.setattr(ImageIngestorService, "download_image", mock_download)

    # Search filtering by brand "Nike"
    payload = {
        "image_url": "https://picsum.photos/blue.png",
        "brand": "Nike"
    }
    res = client.post("/api/v1/search/url", json=payload)
    assert res.status_code == 200
    data = res.json()
    for item in data["results"]:
        assert item["brand"] == "Nike"
        assert item["id"] == "premium-shoes"


def test_multimodal_text_query_and_cache(monkeypatch):
    mock_bytes = generate_test_image_bytes(color=(0, 0, 255))
    async def mock_download(*args, **kwargs):
        return mock_bytes
    monkeypatch.setattr(ImageIngestorService, "download_image", mock_download)

    payload_red = {
        "image_url": "https://picsum.photos/blue.png",
        "text_query": "red color tag",
        "image_weight": 0.5
    }

    # First search: Cache Miss
    res1 = client.post("/api/v1/search/url", json=payload_red)
    assert res1.status_code == 200
    assert res1.json()["cache_hit"] is False

    # Second search with same text query: Cache Hit
    res2 = client.post("/api/v1/search/url", json=payload_red)
    assert res2.status_code == 200
    assert res2.json()["cache_hit"] is True

    # Third search with DIFFERENT text query on same image: Cache Miss (key distinct check)
    payload_blue = {
        "image_url": "https://picsum.photos/blue.png",
        "text_query": "blue color tag",
        "image_weight": 0.5
    }
    res3 = client.post("/api/v1/search/url", json=payload_blue)
    assert res3.status_code == 200
    assert res3.json()["cache_hit"] is False
