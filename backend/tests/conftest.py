"""
Pytest configuration and fixtures for Interior AI Backend tests

This module provides shared fixtures and configuration for all tests including:
- Test database setup and teardown
- Test Redis connection
- Mock external services (Replicate, S3)
- Test client for API testing
- Sample data fixtures
"""

import os
import pytest
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.session import Base, get_db
from app.core.config import settings
from app.models.user import User, SubscriptionTier
from app.models.transformation import Transformation, TransformationStatus
from app.core.security import get_password_hash

# Test database configuration
TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    """Create a fresh database for each test"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db: Session) -> Generator[TestClient, None, None]:
    """Create a test client with database dependency override"""
    def override_get_db():
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db: Session) -> User:
    """Create a test user"""
    user = User(
        email="test@example.com",
        password_hash=get_password_hash("testpassword123"),
        name="Test User",
        credits=10,
        subscription_tier=SubscriptionTier.FREE,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_pro_user(db: Session) -> User:
    """Create a test pro user"""
    user = User(
        email="pro@example.com",
        password_hash=get_password_hash("propassword123"),
        name="Pro User",
        credits=100,
        subscription_tier=SubscriptionTier.PRO,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def auth_headers(client: TestClient, test_user: User) -> dict:
    """Get authentication headers for test user"""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "testpassword123"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def pro_auth_headers(client: TestClient, test_pro_user: User) -> dict:
    """Get authentication headers for pro user"""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "pro@example.com", "password": "propassword123"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sample_transformation(db: Session, test_user: User) -> Transformation:
    """Create a sample transformation"""
    transformation = Transformation(
        user_id=test_user.id,
        job_id="test-job-123",
        status=TransformationStatus.COMPLETED,
        original_image_url="https://example.com/original.jpg",
        transformed_image_url="https://example.com/transformed.jpg",
        vibe="modern",
        colors="neutral",
        description="A beautiful modern living room",
        processing_time_seconds=45.5,
        model_used="adirik/interior-design",
        prompt_used="modern, neutral colors, beautiful living room"
    )
    db.add(transformation)
    db.commit()
    db.refresh(transformation)
    return transformation


@pytest.fixture
def mock_replicate_service(monkeypatch):
    """Mock Replicate API service"""
    class MockReplicateService:
        @staticmethod
        def transform_interior(image_url, prompt, negative_prompt, **kwargs):
            return "https://example.com/transformed-mock.jpg"

    from app.services import replicate_service
    monkeypatch.setattr(replicate_service, "ReplicateService", MockReplicateService)
    return MockReplicateService


@pytest.fixture
def mock_s3_service(monkeypatch):
    """Mock S3 service"""
    class MockS3Service:
        @staticmethod
        def upload_file(file, folder, filename=None):
            return f"https://cdn.example.com/{folder}/{filename or 'test.jpg'}"

        @staticmethod
        def delete_file(url):
            return True

        @staticmethod
        def download_file(url):
            return b"fake image data"

    from app.services import s3_service
    monkeypatch.setattr(s3_service, "S3Service", MockS3Service)
    return MockS3Service


@pytest.fixture
def mock_redis(monkeypatch):
    """Mock Redis connection"""
    class MockRedis:
        def __init__(self):
            self.data = {}

        def get(self, key):
            return self.data.get(key)

        def set(self, key, value, ex=None):
            self.data[key] = value
            return True

        def incr(self, key):
            if key not in self.data:
                self.data[key] = 0
            self.data[key] += 1
            return self.data[key]

        def expire(self, key, seconds):
            return True

        def delete(self, key):
            if key in self.data:
                del self.data[key]
            return True

    return MockRedis()


@pytest.fixture
def sample_image_file():
    """Create a sample image file for upload testing"""
    from io import BytesIO
    from PIL import Image

    # Create a simple test image
    img = Image.new('RGB', (800, 600), color='red')
    img_bytes = BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0)

    return ("test_image.jpg", img_bytes, "image/jpeg")


# Environment setup for tests
@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Setup test environment variables"""
    os.environ["ENVIRONMENT"] = "test"
    os.environ["DATABASE_URL"] = TEST_DATABASE_URL
    os.environ["REDIS_URL"] = "redis://localhost:6379/15"
    os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"
    os.environ["REPLICATE_API_TOKEN"] = "test-replicate-token"
    os.environ["AWS_ACCESS_KEY_ID"] = "test-aws-key"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "test-aws-secret"
    os.environ["S3_BUCKET_NAME"] = "test-bucket"
    os.environ["CLOUDFRONT_DOMAIN"] = "cdn.test.com"
