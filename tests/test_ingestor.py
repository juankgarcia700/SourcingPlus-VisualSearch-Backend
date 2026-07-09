import pytest
import io
import numpy as np
from PIL import Image
import httpx
from app.services.ingestor import ImageIngestorService, ProductInput, ProcessedProduct

def generate_test_image_bytes(color=(255, 0, 0), size=(300, 300)) -> bytes:
    img = Image.new("RGB", size, color=color)
    byte_arr = io.BytesIO()
    img.save(byte_arr, format='PNG')
    return byte_arr.getvalue()

def test_process_image_bytes():
    service = ImageIngestorService()
    img_bytes = generate_test_image_bytes()
    
    # Process image
    resized_img, norm_arr = service.process_image_bytes(
        img_bytes, 
        resize_dim=(224, 224),
        normalize_clip=True,
        transpose_channels=True
    )
    
    # Assert dimensions
    assert resized_img.size == (224, 224)
    assert resized_img.mode == "RGB"
    
    # Assert numpy array shape (Channels, Height, Width)
    assert norm_arr.shape == (3, 224, 224)
    assert norm_arr.dtype == np.float32

@pytest.mark.asyncio
async def test_ingest_product_failure():
    service = ImageIngestorService()
    product = ProductInput(
        id="test-fail-001",
        image_url="http://invalid-url-that-does-not-exist.abc/img.jpg",
        metadata={"sku": "FAIL-001"}
    )
    
    result = await service.ingest_product(product)
    assert result.success is False
    assert result.processed_image is None
    assert result.normalized_array is None
    assert "Network request error" in result.error_message or "Unexpected download failure" in result.error_message
