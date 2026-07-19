from sqlalchemy import Column, String, Float, Integer, DateTime, Boolean
from datetime import datetime, timezone
from app.database import Base

class Product(Base):
    __tablename__ = "products"

    # id matches the string identifier used for vector indexing in Pinecone
    id = Column(String, primary_key=True, index=True)
    sku = Column(String, index=True, nullable=False)
    title = Column(String, nullable=True)
    description = Column(String, nullable=True)
    price = Column(Float, nullable=False)
    category = Column(String, index=True, nullable=False)
    inventory = Column(Integer, nullable=False)
    image_url = Column(String, nullable=False)
    brand = Column(String, nullable=True)
    product_url = Column(String, nullable=True)

    def to_dict(self):
        """Converts model attributes to a dictionary representation."""
        return {
            "id": self.id,
            "sku": self.sku,
            "title": self.title,
            "description": self.description,
            "price": self.price,
            "category": self.category,
            "inventory": self.inventory,
            "image_url": self.image_url,
            "brand": self.brand,
            "product_url": self.product_url
        }


class SearchLog(Base):
    __tablename__ = "search_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    query_type = Column(String, nullable=False)        # "url" or "file"
    query_value = Column(String, nullable=True)         # Image URL or filename
    text_query = Column(String, nullable=True)          # Associated text search input if any
    took_ms = Column(Integer, nullable=False)           # Search execution time in ms
    cache_hit = Column(Boolean, nullable=False)         # Cache status
    top_match_id = Column(String, nullable=True)        # ID of the top returned product
    top_match_score = Column(Float, nullable=True)      # Cosine score of the top returned product

