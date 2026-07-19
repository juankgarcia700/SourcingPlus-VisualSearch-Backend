# Implementation Plan - Phase 6: Multimodal Hybrid Search & Range Filtering

This plan outlines the architecture and execution steps for building Phase 6 of the **SourcingPlus Visual Search Backend**. It introduces hybrid search capabilities, combining query images with unstructured text search and advanced numerical range filters (e.g., price ranges) in Pinecone.

## Goal Description
Build a multimodal visual search engine that supports:
1. **Dense Vector Blending (Multimodal Query)**: Combining a query image embedding with a query text embedding (using CLIP's text encoder) to allow natural language description queries (e.g., searching with an image of a shoe and typing "blue", "sports", or "leather").
2. **Numeric Range Filters**: Allowing queries to specify `min_price` and `max_price`, transforming them into Pinecone logical range filters (`{"price": {"$gte": min, "$lte": max}}`).
3. **Strict Metadata Filters**: Supporting brand-specific and category-specific filtering directly in Pinecone.
4. **FastAPI Contract Integration**: Extending search schemas (`SearchURLPayload`) to support `text_query`, `min_price`, `max_price`, and `brand`.

---

## Technical Specifications

### 1. Vector Blending Algorithm (Multimodal)
When both an `image` and a `text_query` are provided:
1. We compute the normalized image embedding vector $\vec{v}_{img}$ (512-dim).
2. We compute the normalized text embedding vector $\vec{v}_{txt}$ (512-dim) using CLIP's text encoder.
3. We blend the two vectors using a weighting factor $\alpha$ (default: `0.7` for image, `0.3` for text):
   $$\vec{v}_{blended} = \alpha \vec{v}_{img} + (1 - \alpha) \vec{v}_{txt}$$
4. We normalize $\vec{v}_{blended}$ to unit length and run the query against Pinecone.
*In mock mode, the mock generator will deterministically incorporate the text query's hash into the mock vector.*

### 2. Numerical Filters Mapping
Pinecone metadata filters will be built dynamically:
```python
filters = {}
# Range filtering for prices
price_filter = {}
if min_price is not None:
    price_filter["$gte"] = float(min_price)
if max_price is not None:
    price_filter["$lte"] = float(max_price)
if price_filter:
    filters["price"] = price_filter

# Inventory and metadata filters
if in_stock_only:
    filters["inventory"] = {"$gt": 0}
if category:
    filters["category"] = {"$eq": category}
if brand:
    filters["brand"] = {"$eq": brand}
```

---

## User Review Required

> [!IMPORTANT]
> **CLIP Text Encoder Dependencies**
> To support text embedding generation, we will initialize CLIP's text encoder alongside the vision encoder. If `USE_MOCK_EMBEDDINGS=True` is enabled, the mock generator will simulate this blending locally.

> [!TIP]
> **Image Weight Customization**
> We propose introducing a parameter `image_weight` (float, default: `0.7`, range: `0.0` to `1.0`) in the query payload, allowing frontend clients to tune whether they want the search to favor visual similarity (`1.0`) or text instructions (`0.0`).

---

## Open Questions

> [!WARNING]
> 1. **Price Filtering Fallback**: If a product has no price indexed (for legacy data), Pinecone metadata queries with range filters will exclude it. This is standard behavior. We assume all products have valid pricing.

---

## Proposed Changes

### Component: Schemas

#### [MODIFY] [app/schemas.py](file:///c:/Users/GarciaJ26/OneDrive - AkzoNobel/Mundial - Documents/DASHBOARDS & KPI´s/SourcingPlus-VisualSearch-Backend/app/schemas.py)
*   Update `SearchURLPayload` to include `text_query`, `image_weight`, `min_price`, `max_price`, and `brand`.
*   Update `/search/file` query parameters to include these parameters.

---

### Component: AI & Vectorizer Services

#### [MODIFY] [app/services/vectorizer.py](file:///c:/Users/GarciaJ26/OneDrive - AkzoNobel/Mundial - Documents/DASHBOARDS & KPI´s/SourcingPlus-VisualSearch-Backend/app/services/vectorizer.py)
*   Implement CLIP text embedding extraction inside `generate_embedding` when text is passed.
*   Update `query_similar_products` to handle vector blending and range filters.
*   Update `MockPineconeIndex.query` to support Pinecone numeric range filters (`$gte`, `$lte`).

---

### Component: API Endpoints

#### [MODIFY] [app/api/endpoints.py](file:///c:/Users/GarciaJ26/OneDrive - AkzoNobel/Mundial - Documents/DASHBOARDS & KPI´s/SourcingPlus-VisualSearch-Backend/app/api/endpoints.py)
*   Pass new parameters (`text_query`, `image_weight`, `min_price`, `max_price`, `brand`) from `/search/url` and `/search/file` into the vectorizer service.

---

### Verification and Testing

#### [NEW] [tests/test_hybrid.py](file:///c:/Users/GarciaJ26/OneDrive - AkzoNobel/Mundial - Documents/DASHBOARDS & KPI´s/SourcingPlus-VisualSearch-Backend/tests/test_hybrid.py)
Create integration tests verifying:
- Numerical range filtering (`price` bounds).
- Text blending (verifying vector adjusts based on text input).
- Brand-specific filtering.
- Hybrid searching via both url and file uploads.
