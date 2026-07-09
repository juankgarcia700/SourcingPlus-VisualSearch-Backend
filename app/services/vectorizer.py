import os
import io
import logging
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Union, Optional

import numpy as np
try:
    import torch
    torch_available = True
except ImportError:
    torch_available = False
from PIL import Image

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import settings from app.core.config, fallback to env/dotenv if not available
try:
    from app.config import settings
except ImportError:
    logger.info("app.core.config not found. Loading local settings from environment/dotenv.")
    try:
        from pydantic_settings import BaseSettings, SettingsConfigDict
        
        class LocalSettings(BaseSettings):
            pinecone_api_key: str = "mock-key-for-testing"
            pinecone_index_name: str = "sourcingplus-visual-search"
            use_mock_embeddings: bool = True
            
            model_config = SettingsConfigDict(
                env_file=".env",
                env_file_encoding="utf-8",
                extra="ignore"
            )
            
        settings = LocalSettings()
    except Exception as e:
        logger.warning(f"Failed to initialize pydantic-settings: {e}. Falling back to os.environ.")
        # Minimal fallback class using os.environ
        class EnvSettings:
            @property
            def pinecone_api_key(self) -> str:
                return os.environ.get("PINECONE_API_KEY", "mock-key-for-testing")
            
            @property
            def pinecone_index_name(self) -> str:
                return os.environ.get("PINECONE_INDEX_NAME", "sourcingplus-visual-search")
                
            @property
            def use_mock_embeddings(self) -> bool:
                val = os.environ.get("USE_MOCK_EMBEDDINGS", "True")
                return val.lower() in ("true", "1", "yes")
                
        settings = EnvSettings()

# --- Mock Pinecone Implementation for offline/testing environments ---
class MockPineconeIndex:
    """Mock implementation of a Pinecone index for offline/test environments."""
    def __init__(self, name: str):
        self.name = name
        self._vectors: Dict[str, Dict[str, Any]] = {}
        
    def upsert(self, vectors: List[Union[tuple, dict]], namespace: Optional[str] = None) -> Dict[str, Any]:
        count = 0
        for vec in vectors:
            if isinstance(vec, tuple):
                if len(vec) == 3:
                    vec_id, values, metadata = vec
                elif len(vec) == 2:
                    vec_id, values = vec
                    metadata = {}
                else:
                    logger.warning(f"Invalid tuple shape for upsert: {len(vec)}")
                    continue
            elif isinstance(vec, dict):
                vec_id = vec.get("id")
                values = vec.get("values")
                metadata = vec.get("metadata", {})
            else:
                logger.warning(f"Unsupported vector data structure: {type(vec)}")
                continue
                
            if not vec_id or values is None:
                logger.warning("Skipping vector upsert: missing ID or values.")
                continue
                
            self._vectors[str(vec_id)] = {
                "values": list(values),
                "metadata": metadata
            }
            count += 1
            
        logger.info(f"[MockPineconeIndex] Upserted {count} vectors.")
        return {"upserted_count": count}

    def query(
        self, 
        vector: List[float], 
        top_k: int = 10, 
        include_values: bool = False, 
        include_metadata: bool = True, 
        namespace: Optional[str] = None,
        filter: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        matches = []
        q_vec = np.array(vector)
        q_norm = np.linalg.norm(q_vec)
        
        for vec_id, data in self._vectors.items():
            metadata = data.get("metadata", {})
            
            # Apply filter evaluation logic
            if filter:
                skip = False
                for field, val_op in filter.items():
                    if not isinstance(val_op, dict):
                        # Simple equality comparison: {"category": "Shirts"}
                        if metadata.get(field) != val_op:
                            skip = True
                            break
                    else:
                        # Operator comparison: {"inventory": {"$gt": 0}}
                        for op, limit in val_op.items():
                            meta_val = metadata.get(field)
                            if meta_val is None:
                                skip = True
                                break
                            if op == "$eq" and meta_val != limit:
                                skip = True
                            elif op == "$gt" and not (meta_val > limit):
                                skip = True
                            elif op == "$lt" and not (meta_val < limit):
                                skip = True
                            elif op == "$gte" and not (meta_val >= limit):
                                skip = True
                            elif op == "$lte" and not (meta_val <= limit):
                                skip = True
                        if skip:
                            break
                if skip:
                    continue

            db_vec = np.array(data["values"])
            db_norm = np.linalg.norm(db_vec)
            
            if q_norm > 0 and db_norm > 0:
                # Cosine similarity
                score = float(np.dot(q_vec, db_vec) / (q_norm * db_norm))
            else:
                score = 0.0
                
            match = {
                "id": vec_id,
                "score": score,
            }
            if include_values:
                match["values"] = data["values"]
            if include_metadata:
                match["metadata"] = data["metadata"]
            matches.append(match)
            
        matches.sort(key=lambda x: x["score"], reverse=True)
        return {"matches": matches[:top_k], "namespace": namespace}

    def describe_index_stats(self) -> Dict[str, Any]:
        return {
            "dimension": 512,
            "index_fullness": 0.0,
            "total_vector_count": len(self._vectors),
            "namespaces": {"": {"vector_count": len(self._vectors)}}
        }

class MockPinecone:
    """Mock implementation of the Pinecone client."""
    def __init__(self, api_key: str):
        self.api_key = api_key
        self._indexes: Dict[str, MockPineconeIndex] = {}

    def Index(self, name: str) -> MockPineconeIndex:
        if name not in self._indexes:
            self._indexes[name] = MockPineconeIndex(name)
        return self._indexes[name]
        
    def list_indexes(self):
        class MockIndexModel:
            def __init__(self, name):
                self.name = name
        
        class IndexList:
            def __init__(self, indexes):
                self._indexes = indexes
            def names(self) -> List[str]:
                return list(self._indexes.keys())
            def __iter__(self):
                return iter(MockIndexModel(name) for name in self._indexes.keys())
        return IndexList(self._indexes)
        
    def create_index(self, name: str, **kwargs):
        if name not in self._indexes:
            self._indexes[name] = MockPineconeIndex(name)
            logger.info(f"[MockPinecone] Created index: {name}")


# --- Initialize Pinecone Database Connection ---
pc_client = None
pc_index = None

def get_pinecone_index():
    """
    Connect to the Pinecone vector database using the pinecone-client library.
    Sets up client and verifies/creates the index 'sourcingplus-visual-search' (serverless).
    """
    global pc_client, pc_index
    if pc_index is not None:
        return pc_index
        
    api_key = settings.pinecone_api_key
    index_name = settings.pinecone_index_name
    use_mock = settings.use_mock_embeddings or api_key in ("mock-key-for-testing", "", None)
    
    if use_mock:
        logger.info("Initializing Mock Pinecone Client...")
        pc_client = MockPinecone(api_key=api_key)
    else:
        try:
            from pinecone import Pinecone
            logger.info("Initializing real Pinecone Client...")
            pc_client = Pinecone(api_key=api_key)
        except Exception as e:
            logger.warning(f"Failed to import/initialize real Pinecone client: {e}. Falling back to Mock.")
            pc_client = MockPinecone(api_key=api_key)
            use_mock = True
            
    try:
        # Check if index exists and create if needed
        indexes_list = pc_client.list_indexes()
        
        # Safe extraction of names from list_indexes() return value across different pinecone-client versions
        if hasattr(indexes_list, "names"):
            names = indexes_list.names()
        else:
            names = []
            for idx in indexes_list:
                if hasattr(idx, "name"):
                    names.append(idx.name)
                elif isinstance(idx, dict) and "name" in idx:
                    names.append(idx["name"])
                else:
                    names.append(str(idx))
                    
        if index_name not in names:
            logger.info(f"Creating Pinecone index: {index_name} (serverless)")
            if use_mock:
                pc_client.create_index(name=index_name)
            else:
                from pinecone import ServerlessSpec
                pc_client.create_index(
                    name=index_name,
                    dimension=512,
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud="aws",
                        region="us-east-1"
                    )
                )
        pc_index = pc_client.Index(index_name)
        logger.info(f"Successfully initialized connection to Pinecone index: {index_name}")
    except Exception as e:
        logger.error(f"Error accessing or creating Pinecone index: {e}. Falling back to mock index.")
        if not isinstance(pc_client, MockPinecone):
            pc_client = MockPinecone(api_key=api_key)
        pc_index = pc_client.Index(index_name)
        
    return pc_index


# --- Initialize CLIP Model ---
if torch_available:
    device = "cuda" if torch.cuda.is_available() else "cpu"
else:
    device = "cpu"
model = None
processor = None
clip_available = False

if not settings.use_mock_embeddings:
    try:
        logger.info(f"Loading CLIP model 'openai/clip-vit-base-patch32' on device: {device}...")
        from transformers import CLIPProcessor, CLIPModel
        model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(device)
        processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
        clip_available = True
        logger.info("CLIP model loaded successfully.")
    except Exception as e:
        logger.error(f"Failed to load CLIP model from Hugging Face: {e}. Fallback mock embedding generator will be used.")
        clip_available = False
else:
    logger.info("Running with mock embeddings. CLIP model will not be loaded.")


def generate_mock_embedding(image: Any) -> List[float]:
    """
    Generate a deterministic, normalized 512-dimension vector based on the image's hash.
    Ensures identical images return the identical embedding for test consistency.
    """
    try:
        if isinstance(image, Image.Image):
            # Create a small thumbnail to hash in order to remain fast
            thumb = image.copy()
            thumb.thumbnail((32, 32))
            byte_arr = io.BytesIO()
            thumb.save(byte_arr, format='PNG')
            img_bytes = byte_arr.getvalue()
        elif isinstance(image, bytes):
            img_bytes = image
        elif isinstance(image, (str, Path)):
            img_path = Path(image)
            if img_path.exists():
                img_bytes = img_path.read_bytes()
            else:
                img_bytes = str(image).encode('utf-8')
        else:
            img_bytes = str(image).encode('utf-8')
            
        hasher = hashlib.sha256(img_bytes)
        seed = int(hasher.hexdigest(), 16) % (2**32)
        rng = np.random.default_rng(seed)
        
        # Draw from standard normal distribution
        vector = rng.normal(size=512)
        # Normalize to unit length (for cosine metric alignment)
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
        return vector.tolist()
    except Exception as e:
        logger.warning(f"Error generating mock embedding: {e}. Returning random vector.")
        vector = np.random.normal(size=512)
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
        return vector.tolist()


def _get_pil_image(image: Any) -> Image.Image:
    """Helper to convert input image object (PIL Image, bytes, or file path) into a PIL Image."""
    if isinstance(image, Image.Image):
        return image
    if isinstance(image, bytes):
        return Image.open(io.BytesIO(image))
    if isinstance(image, (str, Path)):
        return Image.open(image)
    raise ValueError(f"Unsupported image type: {type(image)}")


def generate_embedding(image: Any) -> List[float]:
    """
    Generates a 512-dimensional visual embedding.
    Uses CLIP Model if available and not mocked; otherwise falls back to a high-quality deterministic mock embedding.
    
    Args:
        image: A PIL.Image.Image object, raw bytes, or file path.
        
    Returns:
        A list of 512 floats representing the normalized visual embedding.
    """
    if settings.use_mock_embeddings or not clip_available:
        return generate_mock_embedding(image)
        
    try:
        pil_img = _get_pil_image(image)
        # Ensure image is in RGB mode for CLIP
        if pil_img.mode != "RGB":
            pil_img = pil_img.convert("RGB")
            
        # Preprocess and run CLIP
        inputs = processor(images=pil_img, return_tensors="pt").to(device)
        with torch.no_grad():
            image_features = model.get_image_features(**inputs)
            
        # L2 normalization for cosine similarity
        image_features = image_features / image_features.norm(p=2, dim=-1, keepdim=True)
        embedding = image_features.cpu().numpy()[0].tolist()
        return embedding
    except Exception as e:
        logger.warning(f"CLIP embedding generation failed: {e}. Falling back to mock embedding.")
        return generate_mock_embedding(image)


def upsert_products_to_pinecone(
    products: List[Union[Dict[str, Any], Any]], 
    batch_size: int = 100
) -> Dict[str, Any]:
    """
    Generate embeddings for processed products and upsert them in batches to Pinecone.
    
    Args:
        products: A list of products. Each product can be a dictionary or object containing:
                  - id / product_id (str)
                  - image (PIL Image, bytes, or file path)
                  - sku (str)
                  - price (float)
                  - category (str)
                  - inventory (int)
        batch_size: Size of batches for Pinecone upserts.
        
    Returns:
        A summary dictionary of the operation results:
        {
            "status": "success" | "failed",
            "total_processed": int,
            "total_upserted": int,
            "skipped_count": int
        }
    """
    index = get_pinecone_index()
    upsert_data = []
    skipped_count = 0
    
    for idx, product in enumerate(products):
        try:
            # Extract Product ID (ID as the string identifier of the vector)
            prod_id = (
                getattr(product, "id", None) or 
                (product.get("id") if isinstance(product, dict) else None) or
                getattr(product, "product_id", None) or 
                (product.get("product_id") if isinstance(product, dict) else None)
            )
            if not prod_id:
                logger.warning(f"Product at index {idx} missing 'id' or 'product_id'. Skipping.")
                skipped_count += 1
                continue
                
            # Extract Image
            image = (
                getattr(product, "image", None) or 
                (product.get("image") if isinstance(product, dict) else None)
            )
            if image is None:
                logger.warning(f"Product {prod_id} missing 'image'. Skipping.")
                skipped_count += 1
                continue
                
            # Extract Metadata
            sku = getattr(product, "sku", None) or (product.get("sku", "") if isinstance(product, dict) else "")
            price = getattr(product, "price", None) or (product.get("price", 0.0) if isinstance(product, dict) else 0.0)
            category = getattr(product, "category", None) or (product.get("category", "") if isinstance(product, dict) else "")
            inventory = getattr(product, "inventory", None) or (product.get("inventory", 0) if isinstance(product, dict) else 0)
            
            # Map metadata keys and types to match specification
            metadata = {
                "sku": str(sku),
                "price": float(price),
                "category": str(category),
                "inventory": int(inventory)
            }
            
            # Generate 512-dimension embedding
            embedding = generate_embedding(image)
            
            # Append tuple of (id, values, metadata)
            upsert_data.append((str(prod_id), embedding, metadata))
            
        except Exception as e:
            logger.error(f"Error processing product {idx} for vectorization: {e}. Skipping.")
            skipped_count += 1
            continue
            
    total_upserted = 0
    if not upsert_data:
        logger.info("No valid product data to upsert.")
        return {
            "status": "success",
            "total_processed": len(products),
            "total_upserted": 0,
            "skipped_count": skipped_count
        }
        
    # Batch upsert to Pinecone index
    for i in range(0, len(upsert_data), batch_size):
        batch = upsert_data[i:i + batch_size]
        try:
            index.upsert(vectors=batch)
            total_upserted += len(batch)
            logger.info(f"Upserted batch of {len(batch)} vectors to Pinecone (total {total_upserted}/{len(upsert_data)}).")
        except Exception as e:
            logger.error(f"Failed to upsert batch at range [{i}:{i + len(batch)}] to Pinecone: {e}")
            raise e
            
    return {
        "status": "success" if total_upserted > 0 else "failed",
        "total_processed": len(products),
        "total_upserted": total_upserted,
        "skipped_count": skipped_count
    }


def query_similar_products(
    image: Any, 
    top_k: int = 10, 
    score_threshold: float = 0.0,
    in_stock_only: bool = False,
    category: Optional[str] = None,
    cache_url: Optional[str] = None,
    cache_bytes: Optional[bytes] = None
) -> tuple[List[Dict[str, Any]], bool]:
    """
    Query the Pinecone index using the visual embedding generated from the query image.
    Supports score thresholding, inventory availability filters, category filtering,
    and local embedding cache lookup.
    """
    from app.services.cache import query_cache
    
    embedding = None
    cache_hit = False
    
    # 1. Attempt cache lookup
    if cache_url:
        embedding = query_cache.get_by_url(cache_url)
        if embedding is not None:
            cache_hit = True
            logger.info(f"Query embedding cache HIT for URL: {cache_url}")
    elif cache_bytes:
        embedding = query_cache.get_by_bytes(cache_bytes)
        if embedding is not None:
            cache_hit = True
            logger.info("Query embedding cache HIT for image bytes")
            
    # 2. Cache miss: generate embedding and save
    if embedding is None:
        logger.info("Query embedding cache MISS. Processing and vectorizing image...")
        embedding = generate_embedding(image)
        if cache_url:
            query_cache.set_by_url(cache_url, embedding)
        elif cache_bytes:
            query_cache.set_by_bytes(cache_bytes, embedding)
            
    # 3. Build Pinecone metadata query filters
    filters = {}
    if in_stock_only:
        filters["inventory"] = {"$gt": 0}
    if category:
        filters["category"] = {"$eq": category}
        
    # 4. Execute query
    index = get_pinecone_index()
    query_res = index.query(
        vector=embedding,
        top_k=top_k,
        include_metadata=True,
        filter=filters if filters else None
    )
    
    # 5. Filter by similarity threshold and map responses
    matches = []
    for match in query_res.get("matches", []):
        score = match.get("score", 0.0)
        # Cosine similarity threshold filter
        if score < score_threshold:
            continue
            
        metadata = match.get("metadata", {})
        matches.append({
            "id": match.get("id"),
            "sku": metadata.get("sku", ""),
            "price": metadata.get("price", 0.0),
            "category": metadata.get("category", ""),
            "inventory": metadata.get("inventory", 0),
            "score": score
        })
        
    return matches, cache_hit
