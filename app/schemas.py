from pydantic import BaseModel, Field
from typing import List, Optional, Dict

# --- Phase 1: Ingestion Schemas ---
class ProductItem(BaseModel):
    id: str = Field(..., description="Unique product identifier")
    sku: str = Field(..., description="Stock Keeping Unit")
    title: Optional[str] = Field(default=None, description="Product title/name")
    description: Optional[str] = Field(default=None, description="Detailed product description")
    price: float = Field(..., description="Retail sale price")
    category: str = Field(..., description="Product category name")
    inventory: int = Field(..., description="Available inventory quantity")
    image_url: str = Field(..., description="URL of the product image")
    brand: Optional[str] = Field(default=None, description="Product brand name")
    product_url: Optional[str] = Field(default=None, description="Link to the product page")

class ProductSyncPayload(BaseModel):
    products: List[ProductItem] = Field(..., description="List of products to synchronize")

class SyncResponse(BaseModel):
    status: str = Field(..., description="Overall status of the sync operation")
    processed_count: int = Field(..., description="Number of successfully processed images")
    indexed_count: int = Field(..., description="Number of successfully indexed vectors in Pinecone")
    errors: List[str] = Field(default=[], description="List of error messages encountered during sync")

# --- Phase 2: Next-Gen Search Schemas ---
class SearchURLPayload(BaseModel):
    image_url: str = Field(..., description="URL of the query image")
    top_k: int = Field(default=10, ge=1, le=100, description="Number of matching results to return")
    score_threshold: float = Field(default=0.0, ge=0.0, le=1.0, description="Minimum cosine similarity score filter")
    in_stock_only: bool = Field(default=False, description="If true, only return products with inventory > 0")
    category: Optional[str] = Field(default=None, description="Filter results by category name")
    text_query: Optional[str] = Field(default=None, description="Natural language description tag to blend with query image")
    image_weight: float = Field(default=0.7, ge=0.0, le=1.0, description="A weighting factor (0.0 to 1.0) favoring visual similarity over text query")
    min_price: Optional[float] = Field(default=None, ge=0.0, description="Lower price range bound filter")
    max_price: Optional[float] = Field(default=None, ge=0.0, description="Upper price range bound filter")
    brand: Optional[str] = Field(default=None, description="Filter results by brand name")

class SearchResponseItem(BaseModel):
    id: str = Field(..., description="Product identifier")
    sku: str = Field(..., description="Stock Keeping Unit")
    title: Optional[str] = Field(default=None, description="Product title/name")
    description: Optional[str] = Field(default=None, description="Detailed product description")
    price: float = Field(..., description="Retail price")
    category: str = Field(..., description="Product category")
    inventory: int = Field(..., description="Available inventory")
    brand: Optional[str] = Field(default=None, description="Product brand")
    product_url: Optional[str] = Field(default=None, description="Link to product page")
    score: float = Field(..., description="Cosine similarity score (0.0 to 1.0)")

class SearchResponse(BaseModel):
    results: List[SearchResponseItem] = Field(..., description="Sorted list of matching items")
    took_ms: int = Field(..., description="Time taken to process and execute search in milliseconds")
    cache_hit: bool = Field(..., description="Whether the image embedding was fetched from the local cache")


# --- Phase 7: Analytics Schemas ---
class AnalyticsStatsResponse(BaseModel):
    total_queries: int = Field(..., description="Total number of search queries logged")
    cache_hit_rate: float = Field(..., description="Ratio of cache hits to total queries (0.0 to 1.0)")
    average_took_ms: float = Field(..., description="Average search execution latency in milliseconds")
    query_type_distribution: Dict[str, int] = Field(..., description="Distribution count between url and file search queries")

class TrendingProductItem(BaseModel):
    id: str = Field(..., description="Product identifier")
    sku: str = Field(..., description="Product SKU")
    title: Optional[str] = Field(None, description="Product title")
    brand: Optional[str] = Field(None, description="Product brand name")
    price: float = Field(..., description="Product retail price")
    image_url: str = Field(..., description="Image URL of the product")
    search_hits: int = Field(..., description="Number of times this product was returned as the top result")

class TrendingResponse(BaseModel):
    results: List[TrendingProductItem] = Field(..., description="Top trending products list")
