import asyncio
import io
import logging
from typing import Any, Dict, List, Optional, Tuple, Union

import httpx
import numpy as np
from PIL import Image
from pydantic import BaseModel, Field

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProductInput(BaseModel):
    """
    Input schema representing a product to be ingested.
    """
    id: str = Field(..., description="Unique product identifier (e.g., SKU)")
    image_url: str = Field(..., description="Absolute URL of the product image")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, 
        description="Arbitrary product metadata (e.g., category, price, title)"
    )


class ProcessedProduct(BaseModel):
    """
    Output schema containing the ingestion results.
    Includes the processed PIL image and normalized numpy array if successful.
    """
    id: str = Field(..., description="Unique product identifier")
    image_url: str = Field(..., description="URL of the ingested image")
    metadata: Dict[str, Any] = Field(..., description="Original product metadata")
    success: bool = Field(..., description="Whether ingestion was successful")
    
    # Non-serializable properties (allowed via config) for pipeline ingestion
    processed_image: Optional[Image.Image] = Field(
        default=None, 
        description="The processed PIL Image object (RGB, resized to target dimensions)"
    )
    normalized_array: Optional[np.ndarray] = Field(
        default=None, 
        description="The normalized numpy array ready for the vectorization model"
    )
    error_message: Optional[str] = Field(
        default=None, 
        description="Error description if the ingestion process failed"
    )

    model_config = {
        "arbitrary_types_allowed": True
    }


class ImageIngestorService:
    """
    Service responsible for downloading and preprocessing product images asynchronously.
    """

    def __init__(
        self,
        timeout: float = 10.0,
        max_connections: int = 20,
        max_keepalive_connections: int = 5,
    ):
        """
        Initializes the Image Ingestor Service with HTTP client configuration.

        Args:
            timeout: HTTP request timeout in seconds.
            max_connections: Maximum concurrent connection limit.
            max_keepalive_connections: Maximum number of keep-alive connections in pool.
        """
        self.timeout = timeout
        self.limits = httpx.Limits(
            max_connections=max_connections,
            max_keepalive_connections=max_keepalive_connections,
        )

    async def download_image(self, url: str, client: httpx.AsyncClient) -> bytes:
        """
        Asynchronously downloads an image from the specified URL.

        Args:
            url: The absolute image URL.
            client: Active httpx.AsyncClient instance.

        Returns:
            bytes: The raw image file bytes.
            
        Raises:
            RuntimeError: If download fails due to network, status, or protocol errors.
        """
        try:
            response = await client.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            # Warn if content-type does not indicate an image, but do not fail early
            content_type = response.headers.get("content-type", "")
            if not content_type.startswith("image/"):
                logger.warning(
                    f"URL {url} returned non-image content type: '{content_type}'. "
                    "Attempting to process anyway."
                )
                
            return response.content
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP status error {e.response.status_code} downloading {url}")
            raise RuntimeError(f"HTTP status error: {e.response.status_code}") from e
        except httpx.RequestError as e:
            logger.error(f"Request error occurred while downloading {url}: {str(e)}")
            raise RuntimeError(f"Network request error: {str(e)}") from e
        except Exception as e:
            logger.error(f"Unexpected error downloading {url}: {str(e)}")
            raise RuntimeError(f"Unexpected download failure: {str(e)}") from e

    def process_image_bytes(
        self,
        image_bytes: bytes,
        resize_dim: Tuple[int, int] = (224, 224),
        normalize_clip: bool = True,
        transpose_channels: bool = True
    ) -> Tuple[Image.Image, np.ndarray]:
        """
        Decodes raw image bytes, converts them to RGB, resizes, and normalizes pixel values.

        Normalization Modes:
        1. Simple division by 255.0 to scale pixel values into [0.0, 1.0].
        2. Optional CLIP-specific normalization using ImageNet/CLIP mean & standard deviation.
        
        Args:
            image_bytes: Raw bytes of the image file.
            resize_dim: Target resolution as a (width, height) tuple. Default: (224, 224).
            normalize_clip: If True, applies standard CLIP mean/std normalization.
            transpose_channels: If True, returns channels-first format (C, H, W) 
                                preferred by PyTorch. Otherwise returns (H, W, C).

        Returns:
            Tuple[Image.Image, np.ndarray]:
                - The resized RGB PIL Image.
                - The normalized float32 numpy array.
                
        Raises:
            ValueError: If the bytes are corrupt or not a valid image format.
        """
        try:
            # Load the image from bytes
            image = Image.open(io.BytesIO(image_bytes))
        except Exception as e:
            logger.error(f"Failed to decode image bytes: {str(e)}")
            raise ValueError(f"Invalid image format: {str(e)}") from e

        # Ensure the image is in RGB format (handles PNG alpha channels, grayscale, CMYK, etc.)
        if image.mode != "RGB":
            image = image.convert("RGB")

        # Resize image using Bilinear interpolation (standard for CLIP preprocessing)
        resized_image = image.resize(resize_dim, Image.Resampling.BILINEAR)

        # Convert to numpy float32 array and scale pixels to [0, 1]
        np_image = np.array(resized_image, dtype=np.float32) / 255.0

        if normalize_clip:
            # CLIP/ImageNet standard channel mean and standard deviation
            mean = np.array([0.48145466, 0.4578275, 0.40821073], dtype=np.float32)
            std = np.array([0.26862954, 0.26130258, 0.27577711], dtype=np.float32)
            # Apply channel-wise normalization: (pixel - mean) / std
            np_image = (np_image - mean) / std

        if transpose_channels:
            # Convert from standard HWC (Height, Width, Channels) to CHW (Channels, Height, Width)
            np_image = np.transpose(np_image, (2, 0, 1))

        return resized_image, np_image

    async def ingest_product(
        self,
        product: ProductInput,
        client: Optional[httpx.AsyncClient] = None,
        resize_dim: Tuple[int, int] = (224, 224),
        normalize_clip: bool = True,
        transpose_channels: bool = True
    ) -> ProcessedProduct:
        """
        Downloads and processes a single product image.

        Args:
            product: The ProductInput item containing ID, URL, and metadata.
            client: Optional pre-existing AsyncClient. If None, one will be created.
            resize_dim: Target resolution tuple (width, height).
            normalize_clip: Whether to apply CLIP normalization.
            transpose_channels: Whether to convert to channels-first (C, H, W).

        Returns:
            ProcessedProduct: Details of the processed product, including success status
                              and errors if any.
        """
        try:
            if client is None:
                async with httpx.AsyncClient(limits=self.limits, follow_redirects=True) as local_client:
                    image_bytes = await self.download_image(product.image_url, local_client)
            else:
                image_bytes = await self.download_image(product.image_url, client)

            processed_image, normalized_array = self.process_image_bytes(
                image_bytes,
                resize_dim=resize_dim,
                normalize_clip=normalize_clip,
                transpose_channels=transpose_channels
            )

            return ProcessedProduct(
                id=product.id,
                image_url=product.image_url,
                metadata=product.metadata,
                success=True,
                processed_image=processed_image,
                normalized_array=normalized_array
            )

        except Exception as e:
            logger.error(
                f"Ingestion failed for product {product.id} (URL: {product.image_url}): {str(e)}"
            )
            return ProcessedProduct(
                id=product.id,
                image_url=product.image_url,
                metadata=product.metadata,
                success=False,
                error_message=str(e)
            )

    async def ingest_products(
        self,
        products: List[ProductInput],
        concurrency_limit: int = 10,
        resize_dim: Tuple[int, int] = (224, 224),
        normalize_clip: bool = True,
        transpose_channels: bool = True
    ) -> List[ProcessedProduct]:
        """
        Downloads and processes a list of products concurrently, respecting a concurrency limit.

        Args:
            products: List of ProductInput items to process.
            concurrency_limit: Maximum concurrent HTTP requests / image process operations.
            resize_dim: Target resolution tuple (width, height).
            normalize_clip: Whether to apply CLIP normalization.
            transpose_channels: Whether to convert to channels-first (C, H, W).

        Returns:
            List[ProcessedProduct]: Complete list of processed products.
        """
        semaphore = asyncio.Semaphore(concurrency_limit)

        async with httpx.AsyncClient(limits=self.limits, follow_redirects=True) as client:
            
            async def worker(product: ProductInput) -> ProcessedProduct:
                async with semaphore:
                    return await self.ingest_product(
                        product=product,
                        client=client,
                        resize_dim=resize_dim,
                        normalize_clip=normalize_clip,
                        transpose_channels=transpose_channels
                    )
            
            tasks = [worker(product) for product in products]
            return await asyncio.gather(*tasks)
