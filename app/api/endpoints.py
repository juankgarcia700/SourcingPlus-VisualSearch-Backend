from fastapi import APIRouter, HTTPException, File, UploadFile, Query, Depends, BackgroundTasks
from typing import List, Optional
import logging
import time
import httpx
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.schemas import (
    ProductSyncPayload, 
    SyncResponse, 
    SearchURLPayload, 
    SearchResponse, 
    SearchResponseItem,
    AnalyticsStatsResponse,
    TrendingResponse,
    TrendingProductItem
)
from app.services.ingestor import ImageIngestorService, ProductInput
from app.services.vectorizer import upsert_products_to_pinecone, query_similar_products
from app.database import get_db, SessionLocal
from app.models import Product, SearchLog

logger = logging.getLogger(__name__)

router = APIRouter()
ingestor_service = ImageIngestorService()


def record_search_log(
    query_type: str,
    query_value: Optional[str],
    text_query: Optional[str],
    took_ms: int,
    cache_hit: bool,
    top_match_id: Optional[str],
    top_match_score: Optional[float]
):
    """
    Logs search queries to the database asynchronously in a thread-safe database session.
    """
    db = SessionLocal()
    try:
        log_entry = SearchLog(
            query_type=query_type,
            query_value=query_value,
            text_query=text_query,
            took_ms=took_ms,
            cache_hit=cache_hit,
            top_match_id=top_match_id,
            top_match_score=top_match_score
        )
        db.add(log_entry)
        db.commit()
    except Exception as e:
        logger.error(f"Failed to record background search log: {e}")
        db.rollback()
    finally:
        db.close()

@router.get("/health", response_model=dict)
def health_check():
    """
    Checks the status of the service API.
    """
    return {"status": "healthy"}

@router.post("/sync", response_model=SyncResponse)
async def sync_catalog(payload: ProductSyncPayload, db: Session = Depends(get_db)):
    """
    Synchronizes the product catalog by downloading/processing images,
    generating 512-dimension CLIP embeddings, indexing them in Pinecone,
    and persisting rich metadata profiles to the SQL database.
    """
    if not payload.products:
        return SyncResponse(
            status="success",
            processed_count=0,
            indexed_count=0,
            errors=["No products provided in the payload."]
        )

    # 1. Map schemas.ProductItem to ingestor.ProductInput
    product_inputs = []
    for item in payload.products:
        # Create metadata dictionary carrying details needed for vector indexing
        metadata = {
            "sku": item.sku,
            "price": item.price,
            "category": item.category,
            "inventory": item.inventory,
            "title": item.title,
            "description": item.description,
            "brand": item.brand,
            "product_url": item.product_url
        }
        product_inputs.append(
            ProductInput(
                id=item.id,
                image_url=item.image_url,
                metadata=metadata
            )
        )

    logger.info(f"Starting ingestion of {len(product_inputs)} products.")
    
    # 2. Ingest and process images using Pillow
    processed_results = await ingestor_service.ingest_products(product_inputs)

    # 3. Separate successful processing and errors
    success_products = []
    errors = []
    
    for r in processed_results:
        if r.success:
            # Reconstruct dictionary required by vectorizer service
            success_products.append({
                "id": r.id,
                "image": r.processed_image,
                "image_url": r.image_url,
                "sku": r.metadata.get("sku", ""),
                "price": r.metadata.get("price", 0.0),
                "category": r.metadata.get("category", ""),
                "inventory": r.metadata.get("inventory", 0),
                "title": r.metadata.get("title"),
                "description": r.metadata.get("description"),
                "brand": r.metadata.get("brand"),
                "product_url": r.metadata.get("product_url")
            })
        else:
            err_msg = f"Product {r.id} image processing failed: {r.error_message}"
            logger.error(err_msg)
            errors.append(err_msg)

    processed_count = len(success_products)
    logger.info(f"Successfully processed {processed_count}/{len(product_inputs)} product images.")

    if processed_count == 0:
        return SyncResponse(
            status="failed",
            processed_count=0,
            indexed_count=0,
            errors=errors + ["All products failed image download or processing."]
        )

    # 4. Generate embeddings and upsert to Pinecone
    try:
        upsert_res = upsert_products_to_pinecone(success_products)
        indexed_count = upsert_res.get("total_upserted", 0)
        skipped_count = upsert_res.get("skipped_count", 0)
        
        if skipped_count > 0:
            errors.append(f"Vectorizer skipped {skipped_count} products due to missing attributes.")
            
        status = "success" if indexed_count > 0 else "failed"
        
        # 5. Persist rich metadata profiles to SQL Database
        if indexed_count > 0:
            for p in success_products:
                try:
                    db_product = db.query(Product).filter(Product.id == p["id"]).first()
                    if db_product:
                        # Update existing product metadata
                        db_product.sku = p["sku"]
                        db_product.title = p.get("title")
                        db_product.description = p.get("description")
                        db_product.price = p["price"]
                        db_product.category = p["category"]
                        db_product.inventory = p["inventory"]
                        db_product.brand = p.get("brand")
                        db_product.product_url = p.get("product_url")
                        db_product.image_url = p.get("image_url", "")
                    else:
                        # Insert new product metadata
                        db_product = Product(
                            id=p["id"],
                            sku=p["sku"],
                            title=p.get("title"),
                            description=p.get("description"),
                            price=p["price"],
                            category=p["category"],
                            inventory=p["inventory"],
                            brand=p.get("brand"),
                            product_url=p.get("product_url"),
                            image_url=p.get("image_url", "")
                        )
                        db.add(db_product)
                except Exception as db_err:
                    logger.error(f"Failed to stage product {p['id']} to SQL database: {db_err}")
                    errors.append(f"SQL Database stage error for {p['id']}: {str(db_err)}")
            
            try:
                db.commit()
                logger.info(f"Successfully persisted metadata for {processed_count} products to the SQL database.")
            except Exception as commit_err:
                logger.error(f"Failed to commit metadata to SQL database: {commit_err}")
                db.rollback()
                errors.append(f"SQL Database commit error: {str(commit_err)}")
        
        return SyncResponse(
            status=status,
            processed_count=processed_count,
            indexed_count=indexed_count,
            errors=errors
        )
    except Exception as e:
        err_msg = f"Failed to index vectors in Pinecone: {str(e)}"
        logger.error(err_msg)
        errors.append(err_msg)
        return SyncResponse(
            status="failed",
            processed_count=processed_count,
            indexed_count=0,
            errors=errors
        )


@router.post("/search/url", response_model=SearchResponse)
async def search_by_url(payload: SearchURLPayload, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Search for similar products using an image URL.
    Supports multimodal text query blending, numerical price range filters, and brands.
    Hydrates matched IDs with rich metadata from the SQL database.
    """
    start_time = time.perf_counter()
    try:
        from app.services.cache import query_cache
        import hashlib
        
        # Modify cache key to include text query
        cache_url_key = payload.image_url
        if payload.image_url and payload.text_query:
            cache_url_key = f"{payload.image_url}?text_query={payload.text_query}"
            
        cached_embedding = query_cache.get_by_url(cache_url_key)
        cache_hit = cached_embedding is not None
        
        if cache_hit:
            matches, _ = query_similar_products(
                image=None,
                top_k=payload.top_k,
                score_threshold=payload.score_threshold,
                in_stock_only=payload.in_stock_only,
                category=payload.category,
                cache_url=payload.image_url,
                text_query=payload.text_query,
                image_weight=payload.image_weight,
                min_price=payload.min_price,
                max_price=payload.max_price,
                brand=payload.brand
            )
        else:
            logger.info(f"Cache miss for URL: {payload.image_url}. Downloading image...")
            try:
                async with httpx.AsyncClient(follow_redirects=True) as client:
                    image_bytes = await ingestor_service.download_image(payload.image_url, client)
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Failed to download image from URL: {str(e)}")
                
            try:
                resized_image, _ = ingestor_service.process_image_bytes(image_bytes)
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Failed to process image: {str(e)}")
                
            matches, _ = query_similar_products(
                image=resized_image,
                top_k=payload.top_k,
                score_threshold=payload.score_threshold,
                in_stock_only=payload.in_stock_only,
                category=payload.category,
                cache_url=payload.image_url,
                text_query=payload.text_query,
                image_weight=payload.image_weight,
                min_price=payload.min_price,
                max_price=payload.max_price,
                brand=payload.brand
            )
            
        took_ms = int((time.perf_counter() - start_time) * 1000)
        
        # Hydrate matching IDs with database profile sheets
        hydrated_results = []
        for m in matches:
            prod_id = m["id"]
            db_product = db.query(Product).filter(Product.id == prod_id).first()
            if db_product:
                hydrated_results.append(SearchResponseItem(
                    id=prod_id,
                    sku=db_product.sku,
                    title=db_product.title,
                    description=db_product.description,
                    price=db_product.price,
                    category=db_product.category,
                    inventory=db_product.inventory,
                    brand=db_product.brand,
                    product_url=db_product.product_url,
                    score=m["score"]
                ))
            else:
                logger.warning(f"Product {prod_id} found in Pinecone but missing in SQL database. Hydrating with vector metadata fallback.")
                hydrated_results.append(SearchResponseItem(
                    id=prod_id,
                    sku=m.get("sku", ""),
                    title=None,
                    description=None,
                    price=m.get("price", 0.0),
                    category=m.get("category", ""),
                    inventory=m.get("inventory", 0),
                    brand=None,
                    product_url=None,
                    score=m["score"]
                ))
                
        # Log search telemetry asynchronously
        top_match_id = hydrated_results[0].id if hydrated_results else None
        top_match_score = hydrated_results[0].score if hydrated_results else None
        background_tasks.add_task(
            record_search_log,
            "url",
            payload.image_url,
            payload.text_query,
            took_ms,
            cache_hit,
            top_match_id,
            top_match_score
        )
        
        return SearchResponse(
            results=hydrated_results,
            took_ms=took_ms,
            cache_hit=cache_hit
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during visual search by URL: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal search error: {str(e)}")


@router.post("/search/file", response_model=SearchResponse)
async def search_by_file(
    file: UploadFile = File(...),
    top_k: int = Query(10, ge=1, le=100),
    score_threshold: float = Query(0.0, ge=0.0, le=1.0),
    in_stock_only: bool = Query(False),
    category: Optional[str] = Query(None),
    text_query: Optional[str] = Query(None),
    image_weight: float = Query(0.7, ge=0.0, le=1.0),
    min_price: Optional[float] = Query(None, ge=0.0),
    max_price: Optional[float] = Query(None, ge=0.0),
    brand: Optional[str] = Query(None),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """
    Search for similar products using an uploaded image file.
    Supports multimodal text query blending, numerical price range filters, and brands.
    Hydrates matched IDs with rich metadata from the SQL database.
    """
    start_time = time.perf_counter()
    try:
        image_bytes = await file.read()
        if not image_bytes:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")
            
        from app.services.cache import query_cache
        import hashlib
        
        # Modify cache key to include text query hash
        cache_bytes_key = image_bytes
        if image_bytes and text_query:
            text_hash = hashlib.sha256(text_query.encode("utf-8")).digest()
            cache_bytes_key = image_bytes + text_hash
            
        cached_embedding = query_cache.get_by_bytes(cache_bytes_key)
        cache_hit = cached_embedding is not None
        
        if cache_hit:
            matches, _ = query_similar_products(
                image=None,
                top_k=top_k,
                score_threshold=score_threshold,
                in_stock_only=in_stock_only,
                category=category,
                cache_bytes=image_bytes,
                text_query=text_query,
                image_weight=image_weight,
                min_price=min_price,
                max_price=max_price,
                brand=brand
            )
        else:
            try:
                resized_image, _ = ingestor_service.process_image_bytes(image_bytes)
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Invalid image file: {str(e)}")
                
            matches, _ = query_similar_products(
                image=resized_image,
                top_k=top_k,
                score_threshold=score_threshold,
                in_stock_only=in_stock_only,
                category=category,
                cache_bytes=image_bytes,
                text_query=text_query,
                image_weight=image_weight,
                min_price=min_price,
                max_price=max_price,
                brand=brand
            )
            
        took_ms = int((time.perf_counter() - start_time) * 1000)
        
        # Hydrate matching IDs with database profile sheets
        hydrated_results = []
        for m in matches:
            prod_id = m["id"]
            db_product = db.query(Product).filter(Product.id == prod_id).first()
            if db_product:
                hydrated_results.append(SearchResponseItem(
                    id=prod_id,
                    sku=db_product.sku,
                    title=db_product.title,
                    description=db_product.description,
                    price=db_product.price,
                    category=db_product.category,
                    inventory=db_product.inventory,
                    brand=db_product.brand,
                    product_url=db_product.product_url,
                    score=m["score"]
                ))
            else:
                logger.warning(f"Product {prod_id} found in Pinecone but missing in SQL database. Hydrating with vector metadata fallback.")
                hydrated_results.append(SearchResponseItem(
                    id=prod_id,
                    sku=m.get("sku", ""),
                    title=None,
                    description=None,
                    price=m.get("price", 0.0),
                    category=m.get("category", ""),
                    inventory=m.get("inventory", 0),
                    brand=None,
                    product_url=None,
                    score=m["score"]
                ))
                
        # Log search telemetry asynchronously
        top_match_id = hydrated_results[0].id if hydrated_results else None
        top_match_score = hydrated_results[0].score if hydrated_results else None
        background_tasks.add_task(
            record_search_log,
            "file",
            file.filename,
            text_query,
            took_ms,
            cache_hit,
            top_match_id,
            top_match_score
        )
        
        return SearchResponse(
            results=hydrated_results,
            took_ms=took_ms,
            cache_hit=cache_hit
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during visual search by file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal search error: {str(e)}")


@router.get("/analytics/stats", response_model=AnalyticsStatsResponse)
def get_analytics_stats(db: Session = Depends(get_db)):
    """
    Computes visual search stats, including cache hit rates, average times,
    and distribution between url and file-upload search requests.
    """
    try:
        total_queries = db.query(SearchLog).count()
        if total_queries == 0:
            return AnalyticsStatsResponse(
                total_queries=0,
                cache_hit_rate=0.0,
                average_took_ms=0.0,
                query_type_distribution={"url": 0, "file": 0}
            )

        cache_hits = db.query(SearchLog).filter(SearchLog.cache_hit == True).count()
        cache_hit_rate = float(cache_hits) / total_queries

        # Use func.avg to calculate average took_ms
        avg_took_ms = db.query(func.avg(SearchLog.took_ms)).scalar() or 0.0

        # Query type distribution count
        url_count = db.query(SearchLog).filter(SearchLog.query_type == "url").count()
        file_count = db.query(SearchLog).filter(SearchLog.query_type == "file").count()

        return AnalyticsStatsResponse(
            total_queries=total_queries,
            cache_hit_rate=round(cache_hit_rate, 4),
            average_took_ms=round(float(avg_took_ms), 2),
            query_type_distribution={"url": url_count, "file": file_count}
        )
    except Exception as e:
        logger.error(f"Failed to fetch analytics statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Database aggregation error: {str(e)}")


@router.get("/analytics/trending", response_model=TrendingResponse)
def get_trending_products(top_k: int = Query(5, ge=1, le=50), db: Session = Depends(get_db)):
    """
    Calculates top trending items returned as the #1 best match in visual searches.
    """
    try:
        # Group search logs by top_match_id and count occurrences
        results = (
            db.query(SearchLog.top_match_id, func.count(SearchLog.top_match_id).label("hits"))
            .filter(SearchLog.top_match_id.isnot(None))
            .group_by(SearchLog.top_match_id)
            .order_by(func.count(SearchLog.top_match_id).desc())
            .limit(top_k)
            .all()
        )

        trending_items = []
        for match_id, hits in results:
            # Query Product details for metadata enrichment
            prod = db.query(Product).filter(Product.id == match_id).first()
            if prod:
                trending_items.append(TrendingProductItem(
                    id=prod.id,
                    sku=prod.sku,
                    title=prod.title,
                    brand=prod.brand,
                    price=prod.price,
                    image_url=prod.image_url,
                    search_hits=hits
                ))
            else:
                # Placeholder fallback if product doesn't exist in local metadata DB anymore
                trending_items.append(TrendingProductItem(
                    id=match_id,
                    sku="UNKNOWN",
                    title="Product info not found in DB",
                    brand="Unknown",
                    price=0.0,
                    image_url="",
                    search_hits=hits
                ))

        return TrendingResponse(results=trending_items)
    except Exception as e:
        logger.error(f"Failed to query trending products: {e}")
        raise HTTPException(status_code=500, detail=f"Database aggregation error: {str(e)}")
