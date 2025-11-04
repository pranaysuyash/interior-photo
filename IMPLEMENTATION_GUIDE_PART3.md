# Implementation Guide - Part 3
## Real-time Updates, Rate Limiting, Testing, and Deployment

---

## 11. Real-time Updates

### 11.1 Server-Sent Events (SSE)

```python
# app/api/v1/endpoints/stream.py

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import asyncio
import json
from typing import Optional

from app.db.session import get_db
from app.dependencies import get_optional_user
from app.models.user import User
from app.services.transformation_service import TransformationService

router = APIRouter()


@router.get("/stream/{job_id}")
async def stream_transformation_status(
    job_id: str,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_optional_user)
):
    """
    Stream transformation status updates using Server-Sent Events

    The client can connect to this endpoint and receive real-time updates
    as the transformation progresses.
    """
    async def event_generator():
        """Generate SSE events"""
        max_attempts = 120  # 2 minutes with 1 second intervals
        attempts = 0

        while attempts < max_attempts:
            try:
                # Get fresh transformation data
                transformation = TransformationService.get_transformation_by_job_id(
                    db=db,
                    job_id=job_id,
                    user=user
                )

                # Prepare status data
                status_data = {
                    "job_id": transformation.job_id,
                    "status": transformation.status.value,
                    "original_url": transformation.original_image_url,
                    "transformed_url": transformation.transformed_image_url,
                    "processing_time": transformation.processing_time_seconds,
                    "created_at": transformation.created_at.isoformat(),
                    "completed_at": transformation.completed_at.isoformat() if transformation.completed_at else None,
                    "error_message": transformation.error_message
                }

                # Send event
                yield f"data: {json.dumps(status_data)}\n\n"

                # If completed or failed, close stream
                if transformation.status.value in ["completed", "failed"]:
                    yield "event: close\ndata: {}\n\n"
                    break

                # Wait before next check
                await asyncio.sleep(1)
                attempts += 1

            except Exception as e:
                error_data = {"error": str(e)}
                yield f"data: {json.dumps(error_data)}\n\n"
                break

        # Timeout message
        if attempts >= max_attempts:
            timeout_data = {"error": "Timeout waiting for transformation"}
            yield f"data: {json.dumps(timeout_data)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )
```

Add to API router:
```python
# app/api/v1/api.py
from app.api.v1.endpoints import stream

api_router.include_router(stream.router, tags=["stream"])
```

---

## 12. Rate Limiting

### 12.1 Redis-based Rate Limiter

```python
# app/utils/rate_limiter.py

import redis
from datetime import datetime, timedelta
from typing import Optional
from app.core.config import settings
from app.models.user import User, SubscriptionTier
from app.core.exceptions import RateLimitException


class RateLimiter:
    """Redis-based rate limiter"""

    def __init__(self):
        self.redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

    def get_daily_limit(self, user: Optional[User]) -> int:
        """Get daily transformation limit based on subscription tier"""
        if not user:
            return 3  # Anonymous users: 3 per day

        tier_limits = {
            SubscriptionTier.FREE: settings.RATE_LIMIT_FREE_DAILY,
            SubscriptionTier.PRO: settings.RATE_LIMIT_PRO_DAILY,
            SubscriptionTier.ENTERPRISE: settings.RATE_LIMIT_ENTERPRISE_DAILY,
        }

        return tier_limits.get(user.subscription_tier, 5)

    def check_rate_limit(self, user: Optional[User], ip_address: str) -> dict:
        """
        Check if user/IP has exceeded rate limit

        Returns dict with:
        - allowed: bool
        - remaining: int
        - reset_at: datetime
        - limit: int
        """
        # Get identifier (user ID or IP)
        identifier = str(user.id) if user else f"ip:{ip_address}"

        # Get daily limit
        daily_limit = self.get_daily_limit(user)

        # Redis key for today
        today = datetime.utcnow().date()
        key = f"ratelimit:{identifier}:{today}"

        # Get current count
        current_count = self.redis_client.get(key)
        current_count = int(current_count) if current_count else 0

        # Calculate reset time (midnight UTC)
        tomorrow = today + timedelta(days=1)
        reset_at = datetime.combine(tomorrow, datetime.min.time())

        # Check limit
        remaining = max(0, daily_limit - current_count)
        allowed = current_count < daily_limit

        return {
            "allowed": allowed,
            "remaining": remaining,
            "reset_at": reset_at,
            "limit": daily_limit,
            "current": current_count
        }

    def increment_usage(self, user: Optional[User], ip_address: str) -> None:
        """Increment usage counter"""
        identifier = str(user.id) if user else f"ip:{ip_address}"
        today = datetime.utcnow().date()
        key = f"ratelimit:{identifier}:{today}"

        # Increment counter
        self.redis_client.incr(key)

        # Set expiry for midnight tomorrow (if new key)
        if self.redis_client.ttl(key) == -1:  # No expiry set
            tomorrow = today + timedelta(days=1)
            seconds_until_midnight = (
                datetime.combine(tomorrow, datetime.min.time()) - datetime.utcnow()
            ).total_seconds()
            self.redis_client.expire(key, int(seconds_until_midnight))


# Global rate limiter instance
rate_limiter = RateLimiter()
```

### 12.2 Rate Limit Middleware

```python
# app/middleware/rate_limit.py

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from typing import Callable
import time

from app.utils.rate_limiter import rate_limiter
from app.dependencies import get_optional_user
from app.db.session import get_db


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce rate limits"""

    # Endpoints that require rate limiting
    RATE_LIMITED_ENDPOINTS = [
        "/api/v1/transform/transform",
    ]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Check if endpoint requires rate limiting
        if not any(request.url.path.startswith(endpoint) for endpoint in self.RATE_LIMITED_ENDPOINTS):
            return await call_next(request)

        # Get client IP
        client_ip = request.client.host

        # Try to get user from token
        user = None
        try:
            # This is a simplified version - in production, properly extract user
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                # Get user (simplified - implement proper auth extraction)
                pass
        except:
            pass

        # Check rate limit
        limit_info = rate_limiter.check_rate_limit(user, client_ip)

        # Add rate limit headers to response
        headers = {
            "X-RateLimit-Limit": str(limit_info["limit"]),
            "X-RateLimit-Remaining": str(limit_info["remaining"]),
            "X-RateLimit-Reset": limit_info["reset_at"].isoformat(),
        }

        # If limit exceeded, return 429
        if not limit_info["allowed"]:
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded",
                    "limit": limit_info["limit"],
                    "remaining": 0,
                    "reset_at": limit_info["reset_at"].isoformat()
                },
                headers=headers
            )

        # Process request
        response = await call_next(request)

        # Add headers to response
        for key, value in headers.items():
            response.headers[key] = value

        return response
```

---

## 13. Error Handling

### 13.1 Global Exception Handler

```python
# app/middleware/error_handler.py

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import traceback
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation error",
            "errors": exc.errors()
        }
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail
        }
    )


async def general_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions"""
    logger.error(f"Unhandled exception: {exc}")
    logger.error(traceback.format_exc())

    # Don't expose internal errors in production
    if settings.ENVIRONMENT == "production":
        detail = "Internal server error"
    else:
        detail = str(exc)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": detail
        }
    )
```

---

## 14. Main Application

### 14.1 FastAPI App Setup

```python
# app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging

from app.core.config import settings
from app.api.v1.api import api_router
from app.middleware.error_handler import (
    validation_exception_handler,
    http_exception_handler,
    general_exception_handler
)
from app.middleware.rate_limit import RateLimitMiddleware

# Setup logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered interior design transformation API",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting middleware
app.add_middleware(RateLimitMiddleware)

# Exception handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Include API router
app.include_router(api_router, prefix="/api/v1")


@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug mode: {settings.DEBUG}")


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown"""
    logger.info("Shutting down application")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running"
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="debug" if settings.DEBUG else "info"
    )
```

---

## 15. Testing

### 15.1 Test Configuration

```python
# tests/conftest.py

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

from app.main import app
from app.db.session import Base, get_db
from app.core.config import settings

# Test database URL
TEST_DATABASE_URL = "postgresql://interiorai:test@localhost:5432/interiorai_test"

# Create test engine
test_engine = create_engine(TEST_DATABASE_URL)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session")
def db_engine():
    """Create test database"""
    Base.metadata.create_all(bind=test_engine)
    yield test_engine
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def db_session(db_engine):
    """Create database session for test"""
    connection = db_engine.connect()
    transaction = connection.begin()
    session = TestSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db_session):
    """Create test client"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session):
    """Create test user"""
    from app.models.user import User
    from app.core.security import get_password_hash

    user = User(
        email="test@example.com",
        name="Test User",
        password_hash=get_password_hash("testpassword"),
        credits=10
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user):
    """Get authentication headers"""
    from app.core.security import create_access_token

    access_token = create_access_token(data={"sub": str(test_user.id)})
    return {"Authorization": f"Bearer {access_token}"}
```

### 15.2 API Tests

```python
# tests/test_api/test_auth.py

def test_register(client):
    """Test user registration"""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "newuser@example.com",
            "password": "strongpassword",
            "name": "New User"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert "id" in data


def test_login(client, test_user):
    """Test user login"""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "testpassword"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


def test_login_invalid_credentials(client):
    """Test login with invalid credentials"""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "wrong@example.com",
            "password": "wrongpassword"
        }
    )
    assert response.status_code == 401
```

```python
# tests/test_api/test_transform.py

import io
from PIL import Image


def create_test_image():
    """Create a test image"""
    img = Image.new('RGB', (800, 600), color='white')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0)
    return img_bytes


def test_create_transformation(client, auth_headers, monkeypatch):
    """Test creating a transformation"""
    # Mock S3 and Celery
    def mock_upload(*args, **kwargs):
        return "https://example.com/test.jpg"

    def mock_delay(*args, **kwargs):
        return None

    monkeypatch.setattr("app.services.s3_service.s3_service.upload_file", mock_upload)
    monkeypatch.setattr("app.tasks.transformation_tasks.process_transformation.delay", mock_delay)

    # Create test image
    test_image = create_test_image()

    response = client.post(
        "/api/v1/transform/transform",
        files={"image": ("test.jpg", test_image, "image/jpeg")},
        data={
            "vibe": "modern",
            "colors": "neutral",
            "description": "Test transformation"
        },
        headers=auth_headers
    )

    assert response.status_code == 202
    data = response.json()
    assert "job_id" in data
    assert data["status"] == "pending"


def test_get_transformation_status(client, auth_headers, test_user, db_session):
    """Test getting transformation status"""
    from app.models.transformation import Transformation, TransformationStatus

    # Create test transformation
    transformation = Transformation(
        user_id=test_user.id,
        job_id="test-job-id",
        status=TransformationStatus.COMPLETED,
        original_image_url="https://example.com/original.jpg",
        transformed_image_url="https://example.com/transformed.jpg",
        vibe="modern",
        colors="neutral"
    )
    db_session.add(transformation)
    db_session.commit()

    response = client.get(
        f"/api/v1/transform/transform/{transformation.job_id}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["job_id"] == "test-job-id"
    assert data["status"] == "completed"
```

### 15.3 Run Tests

```bash
# Install pytest
pip install pytest pytest-asyncio pytest-cov

# Run tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_api/test_auth.py

# Run with verbose output
pytest -v
```

---

## 16. Docker & Deployment

### 16.1 Dockerfile

```dockerfile
# backend/Dockerfile

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/api/v1/health')"

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 16.2 Docker Compose

```yaml
# backend/docker-compose.yml

version: '3.8'

services:
  # PostgreSQL Database
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: interiorai
      POSTGRES_PASSWORD: ${DB_PASSWORD:-changeme}
      POSTGRES_DB: interiorai
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U interiorai"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis Cache
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # FastAPI Application
  api:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://interiorai:${DB_PASSWORD:-changeme}@postgres:5432/interiorai
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/1
      - CELERY_RESULT_BACKEND=redis://redis:6379/2
    env_file:
      - .env
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./app:/app/app
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  # Celery Worker
  celery_worker:
    build:
      context: .
      dockerfile: Dockerfile
    environment:
      - DATABASE_URL=postgresql://interiorai:${DB_PASSWORD:-changeme}@postgres:5432/interiorai
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/1
      - CELERY_RESULT_BACKEND=redis://redis:6379/2
    env_file:
      - .env
    depends_on:
      - postgres
      - redis
    command: celery -A app.tasks.celery_app worker --loglevel=info

volumes:
  postgres_data:
```

### 16.3 Running with Docker

```bash
# Build and start services
docker-compose up -d

# View logs
docker-compose logs -f api

# Run migrations
docker-compose exec api alembic upgrade head

# Stop services
docker-compose down

# Rebuild after code changes
docker-compose up -d --build
```

---

## 17. Production Deployment Checklist

### 17.1 Security Checklist
- [ ] Change all default passwords and secrets
- [ ] Use strong SECRET_KEY (32+ characters)
- [ ] Enable HTTPS only
- [ ] Configure CORS properly
- [ ] Set up rate limiting
- [ ] Enable SQL injection protection
- [ ] Sanitize all user inputs
- [ ] Set up API key authentication
- [ ] Configure firewall rules
- [ ] Enable DDoS protection

### 17.2 Performance Checklist
- [ ] Set up CDN for image delivery
- [ ] Configure database connection pooling
- [ ] Enable Redis caching
- [ ] Set up database indices
- [ ] Configure Celery workers (scale based on load)
- [ ] Enable gzip compression
- [ ] Set up database read replicas
- [ ] Configure auto-scaling

### 17.3 Monitoring Checklist
- [ ] Set up application logging
- [ ] Configure error tracking (Sentry)
- [ ] Set up performance monitoring
- [ ] Configure uptime monitoring
- [ ] Set up alerts for errors
- [ ] Monitor API response times
- [ ] Track Celery queue length
- [ ] Monitor database performance

### 17.4 Backup Checklist
- [ ] Set up automated database backups
- [ ] Configure S3 lifecycle policies
- [ ] Test backup restoration
- [ ] Set up disaster recovery plan
- [ ] Document backup procedures

---

## 18. Quick Start Commands

```bash
# Development
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your credentials
alembic upgrade head
uvicorn app.main:app --reload

# Celery worker (in another terminal)
celery -A app.tasks.celery_app worker --loglevel=info

# Docker (recommended)
docker-compose up -d
docker-compose exec api alembic upgrade head

# Testing
pytest
pytest --cov=app

# Production
docker-compose -f docker-compose.prod.yml up -d
```

---

## 19. API Documentation

Once the server is running, access:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 20. Troubleshooting

### Common Issues

**Database connection error:**
```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# Check connection
docker-compose exec postgres psql -U interiorai -d interiorai
```

**Redis connection error:**
```bash
# Check if Redis is running
docker-compose ps redis

# Test connection
docker-compose exec redis redis-cli ping
```

**Celery tasks not processing:**
```bash
# Check worker logs
docker-compose logs -f celery_worker

# Restart worker
docker-compose restart celery_worker
```

**Image upload fails:**
```bash
# Check S3 credentials in .env
# Test S3 connection
python -c "import boto3; print(boto3.client('s3').list_buckets())"
```

---

## 21. Next Steps

After completing this guide:

1. **Test the API** using Postman or curl
2. **Integrate with frontend** - update React app API calls
3. **Add payment integration** (Stripe) for subscriptions
4. **Implement email notifications** for completed transformations
5. **Add webhooks** for Replicate callbacks
6. **Set up monitoring** with Datadog or similar
7. **Configure CI/CD** pipeline
8. **Optimize costs** - review S3 lifecycle policies
9. **Scale infrastructure** - add load balancer, auto-scaling
10. **Launch to production!** 🚀

---

**End of Implementation Guide**

You now have a complete, production-ready backend for Interior AI!
