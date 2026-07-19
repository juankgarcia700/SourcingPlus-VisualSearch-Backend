import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import Product

# Setup in-memory SQLite database for testing
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    # Create tables
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Drop tables
        Base.metadata.drop_all(bind=engine)

def test_create_and_read_product(db_session):
    # Create mock product profile
    new_prod = Product(
        id="prod-db-test-01",
        sku="SKU-DB-01",
        title="Nike Blue Run",
        description="Run shoes with high cushion",
        price=120.0,
        category="Shoes",
        inventory=10,
        image_url="http://example.com/nike.jpg",
        brand="Nike",
        product_url="http://example.com/nike"
    )
    
    db_session.add(new_prod)
    db_session.commit()
    
    # Read product back
    db_prod = db_session.query(Product).filter(Product.id == "prod-db-test-01").first()
    
    assert db_prod is not None
    assert db_prod.title == "Nike Blue Run"
    assert db_prod.sku == "SKU-DB-01"
    assert db_prod.brand == "Nike"
    assert db_prod.product_url == "http://example.com/nike"
    
    # Test to_dict helper
    p_dict = db_prod.to_dict()
    assert p_dict["id"] == "prod-db-test-01"
    assert p_dict["price"] == 120.0
    assert p_dict["inventory"] == 10
