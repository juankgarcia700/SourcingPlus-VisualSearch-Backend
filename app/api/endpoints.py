from fastapi import APIRouter, HTTPException, File, UploadFile, Query
from typing import List, Optional
import logging
import time
import httpx

from app.schemas import (
    ProductSyncPayload, 
    SyncResponse, 
    SearchURLPayload, 
    SearchResponse, 
    SearchResponseItem
)
from app.services.ingestor import ImageIngestorService, ProductInput
from app.services.vectorizer import upsert_products_to_pinecone, query_similar_products

logger = logging.getLogger(__name__)

router = APIRouter()
ingestor_service = ImageIngestorService()

@router.get("/health", response_model=dict)
def health_check():
    """
    Checks the status of the service API.
    """
    return {"status": "healthy"}

@router.post("/sync", response_model=SyncResponse)
async def sync_catalog(payload: ProductSyncPayload):
    """
    Synchronizes the product catalog by downloading/processing images,
    generating 512-dimension CLIP embeddings, and indexing them in Pinecone.
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
            "inventory": item.inventory
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
                "sku": r.metadata.get("sku", ""),
                "price": r.metadata.get("price", 0.0),
                "category": r.metadata.get("category", ""),
                "inventory": r.metadata.get("inventory", 0)
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
async def search_by_url(payload: SearchURLPayload):
    """
    Search for similar products using an image URL.
    Bypasses download and inference if the URL is cached.
    """
    start_time = time.perf_counter()
    try:
        from app.services.cache import query_cache
        
        cached_embedding = query_cache.get_by_url(payload.image_url)
        cache_hit = cached_embedding is not None
        
        if cache_hit:
            matches, _ = query_similar_products(
                image=None,
                top_k=payload.top_k,
                score_threshold=payload.score_threshold,
                in_stock_only=payload.in_stock_only,
                category=payload.category,
                cache_url=payload.image_url
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
                cache_url=payload.image_url
            )
            
        took_ms = int((time.perf_counter() - start_time) * 1000)
        
        results = [SearchResponseItem(**m) for m in matches]
        return SearchResponse(
            results=results,
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
    category: Optional[str] = Query(None)
):
    """
    Search for similar products using an uploaded image file (multipart/form-data).
    Bypasses inference if the file content hash is cached.
    """
    start_time = time.perf_counter()
    try:
        image_bytes = await file.read()
        if not image_bytes:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")
            
        from app.services.cache import query_cache
        
        cached_embedding = query_cache.get_by_bytes(image_bytes)
        cache_hit = cached_embedding is not None
        
        if cache_hit:
            matches, _ = query_similar_products(
                image=None,
                top_k=top_k,
                score_threshold=score_threshold,
                in_stock_only=in_stock_only,
                category=category,
                cache_bytes=image_bytes
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
                cache_bytes=image_bytes
            )
            
        took_ms = int((time.perf_counter() - start_time) * 1000)
        
        results = [SearchResponseItem(**m) for m in matches]
        return SearchResponse(
            results=results,
            took_ms=took_ms,
            cache_hit=cache_hit
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during visual search by file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal search error: {str(e)}")
