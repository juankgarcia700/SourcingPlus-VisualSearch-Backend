import pytest
from fastapi.testclient import TestClient
from PIL import Image
import io
import time

from app.main import app
from app.services.vectorizer import get_pinecone_index, upsert_products_to_pinecone
from app.services.cache import query_cache
from app.services.ingestor import ImageIngestorService
from app.database import SessionLocal, Base, engine
from app.models import Product, SearchLog

client = TestClient(app)

def generate_test_image_bytes(color=(0, 255, 0), size=(224, 224)) -> bytes:
    img = Image.new("RGB", size, color=color)
    byte_arr = io.BytesIO()
    img.save(byte_arr, format='PNG')
    return byte_arr.getvalue()

@pytest.fixture(autouse=True)
def setup_analytics_data():
    # Setup databases
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        db.query(Product).delete()
        db.query(SearchLog).delete()
        db.commit()
    except Exception:
        db.rollback()

    index = get_pinecone_index()
    if hasattr(index, "_vectors"):
        index._vectors.clear()
    query_cache.clear()

    # Seed 2 mock products
    img = Image.new("RGB", (224, 224), color=(0, 255, 0))
    products = [
        {"id": "prod-trending-1", "image": img, "sku": "TRND-01", "price": 10.0, "category": "General", "inventory": 100},
        {"id": "prod-trending-2", "image": img, "sku": "TRND-02", "price": 20.0, "category": "General", "inventory": 50}
    ]
    upsert_products_to_pinecone(products)

    # Seed in SQL
    db_prods = [
        Product(id="prod-trending-1", sku="TRND-01", title="Trending Shoe One", price=10.0, category="General", inventory=100, image_url="http://example.com/1.jpg", brand="Sprint"),
        Product(id="prod-trending-2", sku="TRND-02", title="Trending Shoe Two", price=20.0, category="General", inventory=50, image_url="http://example.com/2.jpg", brand="Sprint")
    ]
    for dp in db_prods:
        db.add(dp)
    db.commit()
    db.close()


def test_search_logging_and_stats(monkeypatch):
    mock_bytes = generate_test_image_bytes()
    async def mock_download(*args, **kwargs):
        return mock_bytes
    monkeypatch.setattr(ImageIngestorService, "download_image", mock_download)

    payload = {
        "image_url": "https://picsum.photos/green.png",
        "top_k": 5
    }

    # Verify initial stats are empty
    res_stats_empty = client.get("/api/v1/analytics/stats")
    assert res_stats_empty.status_code == 200
    assert res_stats_empty.json()["total_queries"] == 0

    # Execute search 1: Cache Miss
    res1 = client.post("/api/v1/search/url", json=payload)
    assert res1.status_code == 200

    # Execute search 2: Cache Hit
    res2 = client.post("/api/v1/search/url", json=payload)
    assert res2.status_code == 200

    # Wait a tiny bit to allow FastAPI BackgroundTasks to write to SQLite
    time.sleep(0.5)

    # Fetch stats and verify telemetry
    res_stats = client.get("/api/v1/analytics/stats")
    assert res_stats.status_code == 200
    data = res_stats.json()
    
    assert data["total_queries"] == 2
    assert data["cache_hit_rate"] == 0.5 # 1 hit out of 2 queries
    assert data["query_type_distribution"]["url"] == 2
    assert data["query_type_distribution"]["file"] == 0


def test_trending_products(monkeypatch):
    mock_bytes = generate_test_image_bytes()
    async def mock_download(*args, **kwargs):
        return mock_bytes
    monkeypatch.setattr(ImageIngestorService, "download_image", mock_download)

    # Create mock search logs directly to simulate searches yielding top results
    db = SessionLocal()
    
    # 3 searches resulting in prod-trending-1 as top match
    for _ in range(3):
        db.add(SearchLog(
            query_type="url",
            query_value="http://example.com/q.jpg",
            took_ms=30,
            cache_hit=False,
            top_match_id="prod-trending-1",
            top_match_score=0.95
        ))
    # 1 search resulting in prod-trending-2 as top match
    db.add(SearchLog(
        query_type="url",
        query_value="http://example.com/q.jpg",
        took_ms=45,
        cache_hit=True,
        top_match_id="prod-trending-2",
        top_match_score=0.88
    ))
    db.commit()
    db.close()

    # Query trending items
    res = client.get("/api/v1/analytics/trending")
    assert res.status_code == 200
    data = res.json()["results"]

    assert len(data) == 2
    # Verify sorting (prod-trending-1 has 3 hits, prod-trending-2 has 1 hit)
    assert data[0]["id"] == "prod-trending-1"
    assert data[0]["search_hits"] == 3
    assert data[0]["title"] == "Trending Shoe One"
    assert data[0]["brand"] == "Sprint"
    
    assert data[1]["id"] == "prod-trending-2"
    assert data[1]["search_hits"] == 1
