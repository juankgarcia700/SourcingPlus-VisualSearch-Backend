# Implementation Plan - Phase 2: Visual Search Endpoint & Querying

This plan outlines the architecture and execution steps for building Phase 2 of the **SourcingPlus Visual Search Backend**. It incorporates next-generation visual search features such as **score thresholds, in-stock filtering, and embedding caching**.

## Goal Description
Build a high-performance visual search pipeline exposed via a clean FastAPI REST interface:
1. **Query Processing**: Accepting query images via file upload (`UploadFile`) or image URL.
2. **Embedding Caching**: Implementing an in-memory query cache that maps image content hashes (for files) and URLs to generated embeddings. If an image is queried repeatedly, we bypass the download and neural model stages to return results instantly (sub-50ms).
3. **Embedding Generation**: Processing query images with Pillow (RGB, 224x224, CLIP normalization) and extracting 512-dimension visual features via CLIP (or mock fallback).
4. **Filtered Pinecone Search**: Querying the serverless Pinecone index with the vector, applying metadata filters, and sorting results by cosine similarity.
5. **Next-Gen API Control**: Exposing fine-grained parameters to control search behavior, such as minimum similarity thresholds and stock availability constraints.

---

## Next-Generation Features & API Parameters

> [!IMPORTANT]
> **Advanced Search Parameters**
> We will add the following parameters to the search endpoints (`/api/v1/search/file` and `/api/v1/search/url`):
> 1. `score_threshold` (float, optional, default: 0.0): If specified, filters out matches with a cosine similarity score below this threshold (e.g., `0.75`), preventing irrelevant product recommendations.
> 2. `in_stock_only` (bool, optional, default: false): If `True`, injects a Pinecone filter `{"inventory": {"$gt": 0}}` to exclude out-of-stock items, improving retail and B2B user experience.
> 3. `category` (str, optional): Injects a Pinecone filter `{"category": {"$eq": category}}` to narrow results.

> [!TIP]
> **Performance Optimization: Local Embedding Caching**
> Generating embeddings via deep learning models (CLIP) is CPU/GPU intensive. We will implement a thread-safe local cache (`app/services/cache.py`) that stores the last 100 generated embeddings by hashing the image bytes or caching the URL. This avoids re-downloading and re-vectorizing common queries.

---

## Open Questions

> [!WARNING]
> 1. **Cache Eviction Policy**: We will use a standard Least Recently Used (LRU) policy with a maximum size of 100 elements. Is this cache size sufficient for the initial testing phase? (We propose 100 as it keeps memory footprint tiny while covering repeat queries).

---

## Proposed Changes

We will modify existing files and introduce a cache utility.

### Component: Cache

#### [NEW] [app/services/cache.py](file:///c:/Users/GarciaJ26/OneDrive - AkzoNobel/Mundial - Documents/DASHBOARDS & KPI´s/SourcingPlus-VisualSearch-Backend/app/services/cache.py)
Implements a simple thread-safe LRU cache for image embeddings to skip model runs on repeat queries.

---

### Component: Data & Schemas

#### [MODIFY] [app/schemas.py](file:///c:/Users/GarciaJ26/OneDrive - AkzoNobel/Mundial - Documents/DASHBOARDS & KPI´s/SourcingPlus-VisualSearch-Backend/app/schemas.py)
Extend schemas to support new parameters and responses:
- `SearchURLPayload`: Includes `image_url`, `top_k`, `score_threshold`, `in_stock_only`, and `category`.
- `SearchResponseItem`: Single product match detail with `score`.
- `SearchResponse`: Output results list and timing metrics (e.g., `took_ms`, `cache_hit`).

---

### Component: AI & Vector Indexing

#### [MODIFY] [app/services/vectorizer.py](file:///c:/Users/GarciaJ26/OneDrive - AkzoNobel/Mundial - Documents/DASHBOARDS & KPI´s/SourcingPlus-VisualSearch-Backend/app/services/vectorizer.py)
Enhance query capability:
- Update `query_similar_products` to accept `score_threshold`, `in_stock_only`, and `category`.
- Integrate metadata query parameters to construct Pinecone query filters.
- Connect caching checks in the vectorization pathway.

---

### Component: API Endpoints

#### [MODIFY] [app/api/endpoints.py](file:///c:/Users/GarciaJ26/OneDrive - AkzoNobel/Mundial - Documents/DASHBOARDS & KPI´s/SourcingPlus-VisualSearch-Backend/app/api/endpoints.py)
Add the next-gen search endpoints:
- `POST /api/v1/search/file` (Multipart/form-data)
- `POST /api/v1/search/url` (JSON)

---

## Verification Plan

### Automated Tests
#### [NEW] [tests/test_search.py](file:///c:/Users/GarciaJ26/OneDrive - AkzoNobel/Mundial - Documents/DASHBOARDS & KPI´s/SourcingPlus-VisualSearch-Backend/tests/test_search.py)
Verifies:
- Cache hits (bypassing model runtime).
- Stock filtering (`in_stock_only` parameter) does not return out-of-stock items.
- Score thresholding (`score_threshold` parameter) filters low-scoring items.
- Category filters work correctly.
