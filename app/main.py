from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.api.endpoints import router as api_router
from app.config import settings
from app.database import Base, engine
import app.models

# Initialize SQL Database tables
Base.metadata.create_all(bind=engine)

# Configure logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="SourcingPlus Visual Search Backend",
    description="Backend service for catalog ingestion, image normalization, CLIP embedding generation, and Pinecone vector indexing.",
    version="1.0.0"
)

# Set up CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes
app.include_router(api_router, prefix="/api/v1", tags=["Catalog Sync"])

@app.get("/")
def read_root():
    return {
        "message": "Welcome to SourcingPlus Visual Search API",
        "version": "1.0.0",
        "docs_url": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting FastAPI development server...")
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
