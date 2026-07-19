# Implementation Plan - Phase 7: Search Analytics & Dashboard Endpoints

This plan outlines the architecture and execution steps for building Phase 7 of the **SourcingPlus Visual Search Backend**. It introduces a logging layer to record search telemetry and exposes endpoints to compute search insights and performance metrics (cache hit rate, search trends, average latency).

## Goal Description
Build an analytics collection and reporting engine:
1. **Search Telemetry Schema**: Add a `SearchLog` model to the relational database to record query type, cache status, execution latency, text query inputs, and top match profiles.
2. **Background Logging Task**: Log search events asynchronously using FastAPI's `BackgroundTasks` to ensure telemetry capture has **zero impact** on search response latency.
3. **Performance Metrics Dashboard Endpoint (`/analytics/stats`)**: Calculate total query counts, cache hit rate percentages, average search latency in milliseconds, and query type distributions.
4. **Visual Search Trends Endpoint (`/analytics/trending`)**: Expose the top $K$ products most frequently returned as the #1 best match in visual searches.

---

## Technical Specifications

### 1. Database Model - `SearchLog`
```python
class SearchLog(Base):
    __tablename__ = "search_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    query_type = Column(String, nullable=False)        # "url" or "file"
    query_value = Column(String, nullable=True)         # URL string or filename
    text_query = Column(String, nullable=True)          # Associated text tag if any
    took_ms = Column(Integer, nullable=False)           # Search execution latency
    cache_hit = Column(Boolean, nullable=False)         # Cache hit telemetry
    top_match_id = Column(String, nullable=True)        # ID of the top product match
    top_match_score = Column(Float, nullable=True)      # Cosine similarity of top match
```

### 2. Async Background Task Integration
To record logs without blocking HTTP responses:
```python
def record_search_log(
    db: Session,
    query_type: str,
    query_value: Optional[str],
    text_query: Optional[str],
    took_ms: int,
    cache_hit: bool,
    results: list
):
    # Extracts top match ID and score from result list and logs entry to SQLite database
    ...
```
In search endpoints, we will inject `background_tasks: BackgroundTasks` and call:
`background_tasks.add_task(record_search_log, ...)`

---

## User Review Required

> [!IMPORTANT]
> **Performance Guarantee**
> Logging to SQLite involves disk I/O, which could add 10-15ms to requests. By executing the logging operation using FastAPI `BackgroundTasks`, we defer disk writes until *after* the HTTP response has been sent to the user. This guarantees that search latency remains unaffected.

---

## Open Questions

> [!WARNING]
> 1. **Data Retention**: For this stage, logs are stored permanently in the local SQLite database. In high-volume production systems, a retention limit or log-rotation script is recommended. For now, we will persist all logs.

---

## Proposed Changes

### Component: Database Models

#### [MODIFY] [app/models.py](file:///c:/Users/GarciaJ26/OneDrive - AkzoNobel/Mundial - Documents/DASHBOARDS & KPI´s/SourcingPlus-VisualSearch-Backend/app/models.py)
*   Add `SearchLog` SQLAlchemy table definition.

---

### Component: Schemas

#### [MODIFY] [app/schemas.py](file:///c:/Users/GarciaJ26/OneDrive - AkzoNobel/Mundial - Documents/DASHBOARDS & KPI´s/SourcingPlus-VisualSearch-Backend/app/schemas.py)
*   Create Pydantic response models for `/analytics/stats` (including hit rates, average times) and `/analytics/trending`.

---

### Component: API Endpoints

#### [MODIFY] [app/api/endpoints.py](file:///c:/Users/GarciaJ26/OneDrive - AkzoNobel/Mundial - Documents/DASHBOARDS & KPI´s/SourcingPlus-VisualSearch-Backend/app/api/endpoints.py)
*   Implement `record_search_log` database operations.
*   Update search endpoints to accept `BackgroundTasks` and queue search log entries.
*   Implement `GET /analytics/stats` endpoint.
*   Implement `GET /analytics/trending` endpoint.

---

### Verification and Testing

#### [NEW] [tests/test_analytics.py](file:///c:/Users/GarciaJ26/OneDrive - AkzoNobel/Mundial - Documents/DASHBOARDS & KPI´s/SourcingPlus-VisualSearch-Backend/tests/test_analytics.py)
Create integration tests verifying:
- Search logs are successfully written on query requests.
- Analytics statistics calculations (total searches, cache hits, latency averages) match the logged records.
- Trending query returns products in sorted order of search hits.
