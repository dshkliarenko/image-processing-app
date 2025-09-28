import asyncio
import os
import tempfile

import cv2
import numpy as np
import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient

# Set test environment variables (for API tests)
os.environ["MONGODB_URL"] = "mongodb://localhost:27017"
os.environ["DATABASE_NAME"] = "test_image_processing_db"
os.environ["COLLECTION_NAME"] = "test_image_results"

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def app():
    """Create FastAPI app for testing"""
    # Import here to ensure environment variables are set
    from app.main import app as fastapi_app
    return fastapi_app

@pytest_asyncio.fixture
async def client():
    """Create async test client"""
    # Import app directly in the fixture
    from app.main import app
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.fixture
def sync_client(app):
    """Create sync test client for simple tests"""
    return TestClient(app)

@pytest.fixture
def sample_image():
    """Create a sample test image"""
    # Create a simple 100x100 RGB image with some pattern
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    # Add some features for SIFT to detect
    cv2.rectangle(img, (20, 20), (80, 80), (255, 255, 255), 2)
    cv2.circle(img, (50, 50), 15, (128, 128, 128), -1)

    # Save to temporary file
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
        cv2.imwrite(temp_file.name, img)
        yield temp_file.name

    # Cleanup
    os.unlink(temp_file.name)

@pytest.fixture
def sample_image_bytes():
    """Create sample image as bytes"""
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    cv2.rectangle(img, (20, 20), (80, 80), (255, 255, 255), 2)
    cv2.circle(img, (50, 50), 15, (128, 128, 128), -1)

    # Encode as JPEG bytes
    _, buffer = cv2.imencode('.jpg', img)
    return buffer.tobytes()

@pytest.fixture
def different_image_bytes():
    """Create a different sample image as bytes"""
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    cv2.rectangle(img, (10, 10), (90, 90), (200, 100, 50), 3)
    cv2.circle(img, (30, 70), 20, (50, 200, 100), -1)

    _, buffer = cv2.imencode('.jpg', img)
    return buffer.tobytes()

# Database cleanup removed - no longer using database integration tests