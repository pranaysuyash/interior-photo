# Complete Backend Implementation Guide
## Interior AI - Step-by-Step Build Guide

This guide will walk you through building the complete backend for Interior AI from scratch, step by step, with full code examples and explanations.

---

## 📋 Table of Contents

1. [Prerequisites & Environment Setup](#1-prerequisites--environment-setup)
2. [Project Structure](#2-project-structure)
3. [Environment Configuration](#3-environment-configuration)
4. [Database Setup](#4-database-setup)
5. [Core Application Setup](#5-core-application-setup)
6. [Authentication System](#6-authentication-system)
7. [Image Storage Service](#7-image-storage-service)
8. [AI Integration (Replicate)](#8-ai-integration-replicate)
9. [Background Job Queue](#9-background-job-queue)
10. [API Endpoints](#10-api-endpoints)
11. [Real-time Updates](#11-real-time-updates)
12. [Rate Limiting](#12-rate-limiting)
13. [Error Handling](#13-error-handling)
14. [Testing](#14-testing)
15. [Deployment](#15-deployment)
16. [Monitoring & Logging](#16-monitoring--logging)

---

## 1. Prerequisites & Environment Setup

### 1.1 System Requirements

```bash
# Required software
- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Node.js 18+ (for frontend)
- Docker & Docker Compose (recommended)
```

### 1.2 Create Virtual Environment

```bash
# Navigate to project directory
cd interior-photo

# Create backend directory
mkdir backend
cd backend

# Create Python virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate
```

### 1.3 Install Dependencies

```bash
# Create requirements.txt
cat > requirements.txt << 'EOF'
# Web Framework
fastapi==0.109.0
uvicorn[standard]==0.27.0
python-multipart==0.0.6

# Database
sqlalchemy==2.0.25
alembic==1.13.1
psycopg2-binary==2.9.9
asyncpg==0.29.0

# Authentication
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-dotenv==1.0.0

# Background Jobs
celery==5.3.6
redis==5.0.1

# AI & Image Processing
replicate==0.22.0
pillow==10.2.0
boto3==1.34.34

# Validation
pydantic==2.5.3
pydantic-settings==2.1.0
email-validator==2.1.0

# Utilities
aiofiles==23.2.1
httpx==0.26.0
python-dateutil==2.8.2

# Monitoring
sentry-sdk==1.40.0

# CORS
fastapi-cors==0.0.6

# Testing
pytest==7.4.4
pytest-asyncio==0.23.3
pytest-cov==4.1.0
httpx==0.26.0
EOF

# Install dependencies
pip install -r requirements.txt
```

### 1.4 Setup PostgreSQL

```bash
# Using Docker (recommended for development)
docker run --name interior-ai-postgres \
  -e POSTGRES_USER=interiorai \
  -e POSTGRES_PASSWORD=your_password_here \
  -e POSTGRES_DB=interiorai \
  -p 5432:5432 \
  -d postgres:15

# Or install PostgreSQL locally
# macOS: brew install postgresql@15
# Ubuntu: sudo apt-get install postgresql-15
```

### 1.5 Setup Redis

```bash
# Using Docker (recommended for development)
docker run --name interior-ai-redis \
  -p 6379:6379 \
  -d redis:7-alpine

# Or install Redis locally
# macOS: brew install redis
# Ubuntu: sudo apt-get install redis-server
```

---

## 2. Project Structure

Create the following directory structure:

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── config.py               # Configuration management
│   ├── dependencies.py         # Dependency injection
│   │
│   ├── api/                    # API routes
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── endpoints/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── auth.py
│   │   │   │   ├── transform.py
│   │   │   │   ├── user.py
│   │   │   │   └── health.py
│   │   │   └── api.py
│   │
│   ├── core/                   # Core functionality
│   │   ├── __init__.py
│   │   ├── security.py         # JWT, password hashing
│   │   ├── config.py           # Settings
│   │   └── exceptions.py       # Custom exceptions
│   │
│   ├── db/                     # Database
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── session.py
│   │   └── init_db.py
│   │
│   ├── models/                 # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── transformation.py
│   │   └── reference_image.py
│   │
│   ├── schemas/                # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── transformation.py
│   │   ├── auth.py
│   │   └── common.py
│   │
│   ├── services/               # Business logic
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── replicate_service.py
│   │   ├── s3_service.py
│   │   ├── prompt_builder.py
│   │   └── transformation_service.py
│   │
│   ├── tasks/                  # Celery tasks
│   │   ├── __init__.py
│   │   ├── celery_app.py
│   │   └── transformation_tasks.py
│   │
│   ├── utils/                  # Utilities
│   │   ├── __init__.py
│   │   ├── image_processor.py
│   │   ├── validators.py
│   │   └── rate_limiter.py
│   │
│   └── middleware/             # Middleware
│       ├── __init__.py
│       ├── rate_limit.py
│       └── error_handler.py
│
├── alembic/                    # Database migrations
│   ├── versions/
│   └── env.py
│
├── tests/                      # Tests
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_api/
│   ├── test_services/
│   └── test_models/
│
├── .env                        # Environment variables
├── .env.example               # Example environment file
├── alembic.ini                # Alembic configuration
├── requirements.txt           # Python dependencies
├── Dockerfile                 # Docker configuration
├── docker-compose.yml         # Docker Compose setup
└── README.md                  # Backend documentation
```

### 2.1 Create Directory Structure

```bash
# From backend/ directory
mkdir -p app/api/v1/endpoints
mkdir -p app/core
mkdir -p app/db
mkdir -p app/models
mkdir -p app/schemas
mkdir -p app/services
mkdir -p app/tasks
mkdir -p app/utils
mkdir -p app/middleware
mkdir -p tests/{test_api,test_services,test_models}
mkdir -p alembic/versions

# Create __init__.py files
touch app/__init__.py
touch app/api/__init__.py
touch app/api/v1/__init__.py
touch app/api/v1/endpoints/__init__.py
touch app/core/__init__.py
touch app/db/__init__.py
touch app/models/__init__.py
touch app/schemas/__init__.py
touch app/services/__init__.py
touch app/tasks/__init__.py
touch app/utils/__init__.py
touch app/middleware/__init__.py
touch tests/__init__.py
```

---

## 3. Environment Configuration

### 3.1 Create .env.example

```bash
cat > .env.example << 'EOF'
# Application
APP_NAME=Interior AI
APP_VERSION=1.0.0
DEBUG=True
ENVIRONMENT=development

# Server
HOST=0.0.0.0
PORT=8000

# Database
DATABASE_URL=postgresql://interiorai:your_password@localhost:5432/interiorai
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=0

# Redis
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=your-super-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# AWS S3
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=us-east-1
S3_BUCKET_NAME=interior-ai-images
S3_BUCKET_URL=https://interior-ai-images.s3.amazonaws.com
CLOUDFRONT_URL=https://d1234567890.cloudfront.net

# Replicate
REPLICATE_API_TOKEN=your_replicate_api_token
REPLICATE_MODEL=adirik/interior-design:76604baddc85a8fdb0b3cad03c9fd9634ff8c64c0e15f74e9f2be61dc63e5c7f

# Celery
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# Rate Limiting
RATE_LIMIT_FREE_DAILY=5
RATE_LIMIT_PRO_DAILY=100
RATE_LIMIT_ENTERPRISE_DAILY=1000

# File Upload
MAX_IMAGE_SIZE_MB=10
ALLOWED_IMAGE_TYPES=jpg,jpeg,png,webp

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# Monitoring
SENTRY_DSN=your_sentry_dsn_here

# Email (for future notifications)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
EOF

# Copy to .env and update with real values
cp .env.example .env
# Edit .env with your actual credentials
```

### 3.2 Create config.py

```python
# app/core/config.py

from pydantic_settings import BaseSettings
from typing import List
import secrets


class Settings(BaseSettings):
    """Application settings"""

    # Application
    APP_NAME: str = "Interior AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Database
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 0

    # Redis
    REDIS_URL: str

    # Security
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # AWS S3
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    AWS_REGION: str = "us-east-1"
    S3_BUCKET_NAME: str
    S3_BUCKET_URL: str
    CLOUDFRONT_URL: str | None = None

    # Replicate
    REPLICATE_API_TOKEN: str
    REPLICATE_MODEL: str

    # Celery
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str

    # Rate Limiting
    RATE_LIMIT_FREE_DAILY: int = 5
    RATE_LIMIT_PRO_DAILY: int = 100
    RATE_LIMIT_ENTERPRISE_DAILY: int = 1000

    # File Upload
    MAX_IMAGE_SIZE_MB: int = 10
    ALLOWED_IMAGE_TYPES: List[str] = ["jpg", "jpeg", "png", "webp"]

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000"

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    # Monitoring
    SENTRY_DSN: str | None = None

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
```

---

## 4. Database Setup

### 4.1 Database Session Management

```python
# app/db/session.py

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Create engine
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    echo=settings.DEBUG,
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db():
    """Dependency for getting database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### 4.2 Database Models

```python
# app/models/user.py

from sqlalchemy import Column, String, Integer, Boolean, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.db.session import Base


class SubscriptionTier(str, enum.Enum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255))
    password_hash = Column(String(255), nullable=False)
    credits = Column(Integer, default=10)
    subscription_tier = Column(
        Enum(SubscriptionTier),
        default=SubscriptionTier.FREE
    )
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    transformations = relationship("Transformation", back_populates="user")

    def __repr__(self):
        return f"<User {self.email}>"
```

```python
# app/models/transformation.py

from sqlalchemy import Column, String, Float, Text, DateTime, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.db.session import Base


class TransformationStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Transformation(Base):
    __tablename__ = "transformations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    job_id = Column(String(255), unique=True, nullable=False, index=True)
    status = Column(
        Enum(TransformationStatus),
        default=TransformationStatus.PENDING,
        index=True
    )

    # Images
    original_image_url = Column(Text, nullable=False)
    transformed_image_url = Column(Text)

    # Parameters
    vibe = Column(String(50))
    colors = Column(String(50))
    description = Column(Text)

    # Processing details
    processing_time_seconds = Column(Float)
    model_used = Column(String(100))
    prompt_used = Column(Text)
    negative_prompt_used = Column(Text)
    error_message = Column(Text)

    # Metadata
    metadata = Column(JSONB)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    completed_at = Column(DateTime)

    # Relationships
    user = relationship("User", back_populates="transformations")
    reference_images = relationship(
        "ReferenceImage",
        back_populates="transformation",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Transformation {self.job_id} - {self.status}>"
```

```python
# app/models/reference_image.py

from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.db.session import Base


class ReferenceImage(Base):
    __tablename__ = "reference_images"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transformation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("transformations.id", ondelete="CASCADE"),
        nullable=False
    )
    image_url = Column(Text, nullable=False)
    image_type = Column(String(50))  # 'furniture', 'color', 'object'
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    transformation = relationship("Transformation", back_populates="reference_images")

    def __repr__(self):
        return f"<ReferenceImage {self.id}>"
```

```python
# app/models/__init__.py

from app.models.user import User, SubscriptionTier
from app.models.transformation import Transformation, TransformationStatus
from app.models.reference_image import ReferenceImage

__all__ = [
    "User",
    "SubscriptionTier",
    "Transformation",
    "TransformationStatus",
    "ReferenceImage",
]
```

### 4.3 Setup Alembic

```bash
# Initialize Alembic
alembic init alembic
```

```python
# alembic/env.py (update the file)

from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# Import your models
from app.db.session import Base
from app.models import User, Transformation, ReferenceImage
from app.core.config import settings

# this is the Alembic Config object
config = context.config

# Set database URL from settings
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Add your model's MetaData object here for 'autogenerate' support
target_metadata = Base.metadata

# ... rest of the file remains the same
```

### 4.4 Create Initial Migration

```bash
# Create initial migration
alembic revision --autogenerate -m "Initial schema"

# Apply migration
alembic upgrade head
```

---

## 5. Core Application Setup

### 5.1 Security Utilities

```python
# app/core/security.py

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import settings

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Create JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def decode_token(token: str) -> dict:
    """Decode and verify JWT token"""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        return None
```

### 5.2 Custom Exceptions

```python
# app/core/exceptions.py

from fastapi import HTTPException, status


class BaseAPIException(HTTPException):
    """Base exception for API errors"""
    def __init__(self, detail: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        super().__init__(status_code=status_code, detail=detail)


class UnauthorizedException(BaseAPIException):
    """Raised when authentication fails"""
    def __init__(self, detail: str = "Not authenticated"):
        super().__init__(detail=detail, status_code=status.HTTP_401_UNAUTHORIZED)


class ForbiddenException(BaseAPIException):
    """Raised when user doesn't have permission"""
    def __init__(self, detail: str = "Not enough permissions"):
        super().__init__(detail=detail, status_code=status.HTTP_403_FORBIDDEN)


class NotFoundException(BaseAPIException):
    """Raised when resource is not found"""
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(detail=detail, status_code=status.HTTP_404_NOT_FOUND)


class ValidationException(BaseAPIException):
    """Raised when validation fails"""
    def __init__(self, detail: str = "Validation error"):
        super().__init__(detail=detail, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)


class RateLimitException(BaseAPIException):
    """Raised when rate limit is exceeded"""
    def __init__(self, detail: str = "Rate limit exceeded"):
        super().__init__(detail=detail, status_code=status.HTTP_429_TOO_MANY_REQUESTS)


class InsufficientCreditsException(BaseAPIException):
    """Raised when user has insufficient credits"""
    def __init__(self, detail: str = "Insufficient credits"):
        super().__init__(detail=detail, status_code=status.HTTP_402_PAYMENT_REQUIRED)
```

---

## 6. Authentication System

### 6.1 Pydantic Schemas

```python
# app/schemas/user.py

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
import uuid


class UserBase(BaseModel):
    email: EmailStr
    name: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=100)


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None


class UserResponse(UserBase):
    id: uuid.UUID
    credits: int
    subscription_tier: str
    is_active: bool
    is_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UserInDB(UserResponse):
    password_hash: str
```

```python
# app/schemas/auth.py

from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: str  # user id
    exp: int  # expiration time


class LoginRequest(BaseModel):
    email: str
    password: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str
```

### 6.2 Auth Service

```python
# app/services/auth_service.py

from sqlalchemy.orm import Session
from typing import Optional
from app.models.user import User
from app.schemas.user import UserCreate
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token
)
from app.core.exceptions import UnauthorizedException


class AuthService:
    @staticmethod
    def create_user(db: Session, user_create: UserCreate) -> User:
        """Create a new user"""
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == user_create.email).first()
        if existing_user:
            raise ValueError("Email already registered")

        # Create user
        user = User(
            email=user_create.email,
            name=user_create.name,
            password_hash=get_password_hash(user_create.password)
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password"""
        user = db.query(User).filter(User.email == email).first()
        if not user:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user

    @staticmethod
    def create_tokens(user_id: str) -> dict:
        """Create access and refresh tokens"""
        access_token = create_access_token(data={"sub": str(user_id)})
        refresh_token = create_refresh_token(data={"sub": str(user_id)})
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }

    @staticmethod
    def get_user_from_token(db: Session, token: str) -> Optional[User]:
        """Get user from JWT token"""
        payload = decode_token(token)
        if not payload:
            return None

        user_id = payload.get("sub")
        if not user_id:
            return None

        user = db.query(User).filter(User.id == user_id).first()
        return user
```

### 6.3 Dependencies

```python
# app/dependencies.py

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional

from app.db.session import get_db
from app.models.user import User
from app.services.auth_service import AuthService
from app.core.exceptions import UnauthorizedException

# Security scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user"""
    token = credentials.credentials
    user = AuthService.get_user_from_token(db, token)

    if not user:
        raise UnauthorizedException("Invalid authentication credentials")

    if not user.is_active:
        raise UnauthorizedException("User account is inactive")

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user"""
    if not current_user.is_active:
        raise UnauthorizedException("Inactive user")
    return current_user


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Get current user if authenticated, None otherwise"""
    if not credentials:
        return None

    token = credentials.credentials
    user = AuthService.get_user_from_token(db, token)
    return user
```

---

## 7. Image Storage Service

### 7.1 S3 Service

```python
# app/services/s3_service.py

import boto3
from botocore.exceptions import ClientError
from datetime import datetime
from typing import BinaryIO, Optional
import uuid
import mimetypes
from app.core.config import settings


class S3Service:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )
        self.bucket_name = settings.S3_BUCKET_NAME
        self.cloudfront_url = settings.CLOUDFRONT_URL or settings.S3_BUCKET_URL

    def upload_file(
        self,
        file: BinaryIO,
        folder: str,
        filename: Optional[str] = None,
        content_type: Optional[str] = None
    ) -> str:
        """
        Upload file to S3

        Args:
            file: File-like object to upload
            folder: S3 folder (e.g., 'originals', 'transformed', 'references')
            filename: Custom filename (optional, will generate UUID if not provided)
            content_type: MIME type (optional, will detect if not provided)

        Returns:
            Public URL of uploaded file
        """
        # Generate filename if not provided
        if not filename:
            ext = self._get_file_extension(file)
            filename = f"{uuid.uuid4()}{ext}"

        # Build S3 key with date-based folder structure
        now = datetime.utcnow()
        key = f"{folder}/{now.year}/{now.month:02d}/{now.day:02d}/{filename}"

        # Detect content type if not provided
        if not content_type:
            content_type = mimetypes.guess_type(filename)[0] or 'application/octet-stream'

        try:
            # Upload to S3
            self.s3_client.upload_fileobj(
                file,
                self.bucket_name,
                key,
                ExtraArgs={
                    'ContentType': content_type,
                    'CacheControl': 'max-age=31536000',  # 1 year cache
                }
            )

            # Return CloudFront URL
            return f"{self.cloudfront_url}/{key}"

        except ClientError as e:
            raise Exception(f"Failed to upload file to S3: {str(e)}")

    def download_file(self, url: str) -> bytes:
        """Download file from S3 URL"""
        # Extract key from URL
        key = url.replace(self.cloudfront_url + "/", "").replace(settings.S3_BUCKET_URL + "/", "")

        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=key)
            return response['Body'].read()
        except ClientError as e:
            raise Exception(f"Failed to download file from S3: {str(e)}")

    def delete_file(self, url: str) -> bool:
        """Delete file from S3"""
        key = url.replace(self.cloudfront_url + "/", "").replace(settings.S3_BUCKET_URL + "/", "")

        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=key)
            return True
        except ClientError as e:
            print(f"Failed to delete file from S3: {str(e)}")
            return False

    def generate_presigned_url(self, key: str, expiration: int = 3600) -> str:
        """Generate presigned URL for private file access"""
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': key},
                ExpiresIn=expiration
            )
            return url
        except ClientError as e:
            raise Exception(f"Failed to generate presigned URL: {str(e)}")

    @staticmethod
    def _get_file_extension(file: BinaryIO) -> str:
        """Get file extension from file object"""
        if hasattr(file, 'name'):
            return '.' + file.name.split('.')[-1]
        return '.jpg'  # Default extension


# Global S3 service instance
s3_service = S3Service()
```

---

## 8. AI Integration (Replicate)

### 8.1 Prompt Builder

```python
# app/services/prompt_builder.py

from typing import Optional


class PromptBuilder:
    """Build optimized prompts for Replicate AI model"""

    # Style descriptions for each vibe
    VIBE_PROMPTS = {
        "modern": "contemporary, clean lines, sleek furniture, minimalist decor, open space",
        "minimalist": "simple, uncluttered, neutral palette, essential furniture only, zen",
        "cozy": "warm, comfortable, inviting, soft textures, ambient lighting, homey",
        "industrial": "exposed brick, metal elements, concrete, Edison bulbs, loft style, urban",
        "bohemian": "eclectic, colorful textiles, plants, vintage pieces, layered decor, artistic",
        "scandinavian": "light wood, white walls, natural materials, hygge, functional, nordic",
        "luxurious": "elegant, high-end materials, chandeliers, plush furniture, ornate, sophisticated",
        "rustic": "wood beams, natural stone, vintage furniture, farmhouse style, country charm"
    }

    # Color palette descriptions
    COLOR_PROMPTS = {
        "neutral": "beige, white, gray, cream, taupe color scheme, subtle tones",
        "warm": "terracotta, amber, rust, golden tones, warm orange and red hues",
        "cool": "blue, teal, mint, cool gray tones, calming colors",
        "earthy": "brown, olive green, terracotta, natural wood tones, earth colors",
        "pastel": "soft pink, lavender, mint, baby blue, muted colors, gentle hues",
        "bold": "vibrant colors, deep jewel tones, saturated hues, dramatic contrast"
    }

    @classmethod
    def build_prompt(
        cls,
        vibe: str,
        colors: str,
        description: Optional[str] = None
    ) -> tuple[str, str]:
        """
        Build positive and negative prompts

        Args:
            vibe: Design vibe/style
            colors: Color palette
            description: Additional user description

        Returns:
            Tuple of (positive_prompt, negative_prompt)
        """
        # Build positive prompt parts
        prompt_parts = [
            f"A {vibe} interior design,",
            cls.VIBE_PROMPTS.get(vibe, "beautiful interior design"),
            f"with {cls.COLOR_PROMPTS.get(colors, 'balanced color scheme')},",
            "photorealistic, high quality, professional photography,",
            "8k resolution, detailed textures, natural lighting,",
            "architectural digest style"
        ]

        # Add user description if provided
        if description and description.strip():
            prompt_parts.insert(3, description.strip())

        positive_prompt = " ".join(prompt_parts)

        # Negative prompt for quality control
        negative_prompt = (
            "ugly, distorted, low quality, blurry, pixelated, "
            "unrealistic, artificial, cartoonish, amateur, "
            "bad proportions, deformed, disfigured, watermark, "
            "text, signature, oversaturated"
        )

        return positive_prompt, negative_prompt

    @classmethod
    def build_prompt_with_references(
        cls,
        vibe: str,
        colors: str,
        description: Optional[str] = None,
        reference_count: int = 0
    ) -> tuple[str, str]:
        """
        Build prompt considering reference images

        Args:
            vibe: Design vibe/style
            colors: Color palette
            description: Additional user description
            reference_count: Number of reference images

        Returns:
            Tuple of (positive_prompt, negative_prompt)
        """
        positive_prompt, negative_prompt = cls.build_prompt(vibe, colors, description)

        # Add reference image context if provided
        if reference_count > 0:
            positive_prompt += (
                f", incorporating similar elements and style from {reference_count} "
                "reference images, matching furniture style, color palette, and aesthetic"
            )

        return positive_prompt, negative_prompt
```

### 8.2 Replicate Service

```python
# app/services/replicate_service.py

import replicate
from typing import Optional
from app.core.config import settings


class ReplicateService:
    """Service for interacting with Replicate AI API"""

    def __init__(self):
        self.api_token = settings.REPLICATE_API_TOKEN
        self.model = settings.REPLICATE_MODEL

        # Set Replicate API token
        replicate.Client(api_token=self.api_token)

    def transform_interior(
        self,
        image_url: str,
        prompt: str,
        negative_prompt: str,
        num_inference_steps: int = 50,
        guidance_scale: float = 7.5,
        seed: Optional[int] = None
    ) -> str:
        """
        Transform interior image using Replicate AI

        Args:
            image_url: URL of the original image
            prompt: Positive prompt describing desired result
            negative_prompt: Negative prompt for quality control
            num_inference_steps: Number of denoising steps (more = better quality but slower)
            guidance_scale: How closely to follow the prompt (7-15 is good range)
            seed: Random seed for reproducibility (optional)

        Returns:
            URL of the transformed image
        """
        input_params = {
            "image": image_url,
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "num_inference_steps": num_inference_steps,
            "guidance_scale": guidance_scale,
        }

        if seed is not None:
            input_params["seed"] = seed

        try:
            # Run the model
            output = replicate.run(
                self.model,
                input=input_params
            )

            # Output is typically a list with one URL
            if isinstance(output, list) and len(output) > 0:
                return output[0]
            elif isinstance(output, str):
                return output
            else:
                raise ValueError(f"Unexpected output format from Replicate: {output}")

        except Exception as e:
            raise Exception(f"Replicate API error: {str(e)}")

    async def transform_interior_async(
        self,
        image_url: str,
        prompt: str,
        negative_prompt: str,
        num_inference_steps: int = 50,
        guidance_scale: float = 7.5,
        seed: Optional[int] = None
    ) -> str:
        """Async version of transform_interior"""
        # Replicate SDK doesn't have native async support yet
        # We'll use this in a background task with Celery
        return self.transform_interior(
            image_url,
            prompt,
            negative_prompt,
            num_inference_steps,
            guidance_scale,
            seed
        )


# Global Replicate service instance
replicate_service = ReplicateService()
```

---

**This is Part 1 of the Implementation Guide. The guide continues with:**

- Part 2: Background Job Queue, API Endpoints, Real-time Updates
- Part 3: Rate Limiting, Testing, Deployment
- Part 4: Complete Code Implementation

Would you like me to continue with the rest of the guide and then proceed to implement the complete backend?
