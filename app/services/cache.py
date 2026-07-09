import collections
import threading
import hashlib
from typing import Dict, List, Optional, Union, Any

class EmbeddingCache:
    """
    Thread-safe Least Recently Used (LRU) cache for storing image embeddings.
    Allows bypassing costly deep learning model (CLIP) inferences for repeat queries.
    """
    def __init__(self, max_size: int = 100):
        self.max_size = max_size
        self.cache: collections.OrderedDict = collections.OrderedDict()
        self.lock = threading.Lock()

    def _generate_bytes_hash(self, data: bytes) -> str:
        """Generates a SHA-256 hash string from raw image bytes."""
        return hashlib.sha256(data).hexdigest()

    def get_by_url(self, url: str) -> Optional[List[float]]:
        """Retrieves cached embedding using the image URL as key."""
        with self.lock:
            if url in self.cache:
                # Move to end to mark as recently used
                self.cache.move_to_end(url)
                return self.cache[url]
            return None

    def get_by_bytes(self, image_bytes: bytes) -> Optional[List[float]]:
        """Retrieves cached embedding using the image bytes SHA-256 hash as key."""
        key = self._generate_bytes_hash(image_bytes)
        with self.lock:
            if key in self.cache:
                self.cache.move_to_end(key)
                return self.cache[key]
            return None

    def set_by_url(self, url: str, embedding: List[float]) -> None:
        """Saves embedding using the image URL as key."""
        with self.lock:
            if url in self.cache:
                self.cache.move_to_end(url)
            self.cache[url] = embedding
            if len(self.cache) > self.max_size:
                # Pop oldest element (FIFO order from start of dict)
                self.cache.popitem(last=False)

    def set_by_bytes(self, image_bytes: bytes, embedding: List[float]) -> None:
        """Saves embedding using the image bytes SHA-256 hash as key."""
        key = self._generate_bytes_hash(image_bytes)
        with self.lock:
            if key in self.cache:
                self.cache.move_to_end(key)
            self.cache[key] = embedding
            if len(self.cache) > self.max_size:
                self.cache.popitem(last=False)

    def clear(self) -> None:
        """Clears all cached entries."""
        with self.lock:
            self.cache.clear()

# Global query cache singleton
query_cache = EmbeddingCache(max_size=100)
