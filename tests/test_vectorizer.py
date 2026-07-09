import pytest
from PIL import Image
from app.services.vectorizer import (
    generate_embedding, 
    generate_mock_embedding, 
    upsert_products_to_pinecone, 
    get_pinecone_index
)

def test_generate_mock_embedding():
    img = Image.new("RGB", (100, 100), color=(0, 255, 0))
    embedding = generate_mock_embedding(img)
    
    assert isinstance(embedding, list)
    assert len(embedding) == 512
    assert all(isinstance(x, float) for x in embedding)
    
    # Check normalization (norm should be close to 1.0)
    import math
    sq_sum = sum(x**2 for x in embedding)
    assert math.isclose(sq_sum, 1.0, rel_tol=1e-5)

def test_generate_embedding_fallback():
    # Will use mock generator because USE_MOCK_EMBEDDINGS is True
    img = Image.new("RGB", (100, 100), color=(0, 0, 255))
    embedding = generate_embedding(img)
    
    assert len(embedding) == 512

def test_upsert_products_to_pinecone():
    index = get_pinecone_index()
    if hasattr(index, "_vectors"):
        index._vectors.clear()
        
    img1 = Image.new("RGB", (224, 224), color=(255, 0, 0))
    img2 = Image.new("RGB", (224, 224), color=(0, 255, 0))
    
    products = [
        {
            "id": "prod-1",
            "image": img1,
            "sku": "SKU-RED-1",
            "price": 19.99,
            "category": "Shirts",
            "inventory": 50
        },
        {
            "id": "prod-2",
            "image": img2,
            "sku": "SKU-GREEN-2",
            "price": 29.99,
            "category": "Pants",
            "inventory": 20
        }
    ]
    
    res = upsert_products_to_pinecone(products)
    assert res["status"] == "success"
    assert res["total_processed"] == 2
    assert res["total_upserted"] == 2
    assert res["skipped_count"] == 0
    
    # Verify in Index
    index = get_pinecone_index()
    stats = index.describe_index_stats()
    assert stats["total_vector_count"] >= 2
    
    # Query test
    query_vec = generate_embedding(img1)
    query_res = index.query(vector=query_vec, top_k=5, include_metadata=True)
    
    assert "matches" in query_res
    assert len(query_res["matches"]) >= 2
    best_match = query_res["matches"][0]
    assert best_match["id"] == "prod-1"
    assert best_match["score"] > 0.95
    assert best_match["metadata"]["sku"] == "SKU-RED-1"
    assert best_match["metadata"]["category"] == "Shirts"
    assert best_match["metadata"]["price"] == 19.99
    assert best_match["metadata"]["inventory"] == 50
