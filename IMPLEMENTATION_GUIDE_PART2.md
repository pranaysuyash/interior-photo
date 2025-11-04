# Implementation Guide - Part 2
## Background Jobs, API Endpoints, Real-time Updates

---

## 9. Background Job Queue

### 9.1 Celery Configuration

```python
# app/tasks/celery_app.py

from celery import Celery
from app.core.config import settings

# Create Celery app
celery_app = Celery(
    "interior_ai",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=['app.tasks.transformation_tasks']
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes max
    task_soft_time_limit=240,  # Soft limit at 4 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,
)
```

### 9.2 Transformation Tasks

```python
# app/tasks/transformation_tasks.py

from celery import Task
from sqlalchemy.orm import Session
import time
import httpx
from datetime import datetime
from typing import Optional

from app.tasks.celery_app import celery_app
from app.db.session import SessionLocal
from app.models.transformation import Transformation, TransformationStatus
from app.services.replicate_service import replicate_service
from app.services.s3_service import s3_service
from app.services.prompt_builder import PromptBuilder


class DatabaseTask(Task):
    """Base task with database session"""
    _db: Optional[Session] = None

    @property
    def db(self) -> Session:
        if self._db is None:
            self._db = SessionLocal()
        return self._db

    def after_return(self, *args, **kwargs):
        if self._db is not None:
            self._db.close()


@celery_app.task(bind=True, base=DatabaseTask, max_retries=3)
def process_transformation(
    self,
    transformation_id: str,
    original_image_url: str,
    vibe: str,
    colors: str,
    description: Optional[str] = None,
    reference_image_count: int = 0
) -> dict:
    """
    Process interior transformation in background

    Args:
        self: Celery task instance
        transformation_id: UUID of transformation record
        original_image_url: S3 URL of original image
        vibe: Design vibe/style
        colors: Color palette
        description: Additional description
        reference_image_count: Number of reference images

    Returns:
        Dictionary with processing results
    """
    start_time = time.time()

    try:
        # Get transformation record
        transformation = self.db.query(Transformation).filter(
            Transformation.id == transformation_id
        ).first()

        if not transformation:
            raise Exception(f"Transformation {transformation_id} not found")

        # Update status to processing
        transformation.status = TransformationStatus.PROCESSING
        self.db.commit()

        # Build prompts
        positive_prompt, negative_prompt = PromptBuilder.build_prompt_with_references(
            vibe=vibe,
            colors=colors,
            description=description,
            reference_count=reference_image_count
        )

        # Call Replicate API
        transformed_url = replicate_service.transform_interior(
            image_url=original_image_url,
            prompt=positive_prompt,
            negative_prompt=negative_prompt,
            num_inference_steps=50,
            guidance_scale=7.5
        )

        # Download transformed image from Replicate
        response = httpx.get(transformed_url)
        response.raise_for_status()

        # Upload to our S3
        from io import BytesIO
        final_url = s3_service.upload_file(
            file=BytesIO(response.content),
            folder="transformed",
            content_type="image/jpeg"
        )

        # Calculate processing time
        processing_time = time.time() - start_time

        # Update transformation record
        transformation.status = TransformationStatus.COMPLETED
        transformation.transformed_image_url = final_url
        transformation.processing_time_seconds = processing_time
        transformation.model_used = "adirik/interior-design"
        transformation.prompt_used = positive_prompt
        transformation.negative_prompt_used = negative_prompt
        transformation.completed_at = datetime.utcnow()
        self.db.commit()

        return {
            "status": "completed",
            "transformation_id": str(transformation_id),
            "transformed_url": final_url,
            "processing_time": processing_time
        }

    except Exception as exc:
        # Update transformation with error
        transformation = self.db.query(Transformation).filter(
            Transformation.id == transformation_id
        ).first()

        if transformation:
            transformation.status = TransformationStatus.FAILED
            transformation.error_message = str(exc)
            self.db.commit()

        # Retry logic
        if self.request.retries < self.max_retries:
            # Exponential backoff: 2, 4, 8 seconds
            countdown = 2 ** self.request.retries
            raise self.retry(exc=exc, countdown=countdown)
        else:
            return {
                "status": "failed",
                "transformation_id": str(transformation_id),
                "error": str(exc)
            }
```

---

## 10. API Endpoints

### 10.1 Pydantic Schemas

```python
# app/schemas/transformation.py

from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List
from datetime import datetime
import uuid


class TransformationCreate(BaseModel):
    vibe: str = Field(..., description="Design vibe/style")
    colors: str = Field(..., description="Color palette")
    description: Optional[str] = Field(None, description="Additional description")


class TransformationResponse(BaseModel):
    id: uuid.UUID
    job_id: str
    status: str
    original_image_url: str
    transformed_image_url: Optional[str] = None
    vibe: str
    colors: str
    description: Optional[str] = None
    processing_time_seconds: Optional[float] = None
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TransformationListResponse(BaseModel):
    transformations: List[TransformationResponse]
    total: int
    limit: int
    offset: int


class TransformationStatusResponse(BaseModel):
    job_id: str
    status: str
    original_url: str
    transformed_url: Optional[str] = None
    processing_time: Optional[float] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    metadata: dict = {}
```

### 10.2 Image Upload Utilities

```python
# app/utils/image_processor.py

from PIL import Image
from io import BytesIO
from typing import Tuple
from app.core.config import settings
from app.core.exceptions import ValidationException


class ImageProcessor:
    """Utility class for image processing and validation"""

    @staticmethod
    def validate_image(file_content: bytes, filename: str) -> None:
        """
        Validate uploaded image

        Args:
            file_content: Image file content
            filename: Original filename

        Raises:
            ValidationException: If image is invalid
        """
        # Check file size
        file_size_mb = len(file_content) / (1024 * 1024)
        if file_size_mb > settings.MAX_IMAGE_SIZE_MB:
            raise ValidationException(
                f"Image size ({file_size_mb:.1f}MB) exceeds maximum allowed "
                f"({settings.MAX_IMAGE_SIZE_MB}MB)"
            )

        # Check file extension
        extension = filename.lower().split('.')[-1]
        if extension not in settings.ALLOWED_IMAGE_TYPES:
            raise ValidationException(
                f"File type '.{extension}' not allowed. "
                f"Allowed types: {', '.join(settings.ALLOWED_IMAGE_TYPES)}"
            )

        # Try to open image
        try:
            image = Image.open(BytesIO(file_content))
            image.verify()
        except Exception as e:
            raise ValidationException(f"Invalid image file: {str(e)}")

    @staticmethod
    def sanitize_image(file_content: bytes) -> bytes:
        """
        Remove EXIF data and optimize image

        Args:
            file_content: Original image content

        Returns:
            Sanitized image content
        """
        # Open image
        image = Image.open(BytesIO(file_content))

        # Remove EXIF data
        data = list(image.getdata())
        image_without_exif = Image.new(image.mode, image.size)
        image_without_exif.putdata(data)

        # Save to bytes
        output = BytesIO()
        image_without_exif.save(output, format='JPEG', quality=95, optimize=True)
        return output.getvalue()

    @staticmethod
    def get_image_dimensions(file_content: bytes) -> Tuple[int, int]:
        """Get image width and height"""
        image = Image.open(BytesIO(file_content))
        return image.size
```

### 10.3 Transformation Service

```python
# app/services/transformation_service.py

from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
import uuid

from app.models.transformation import Transformation, TransformationStatus
from app.models.reference_image import ReferenceImage
from app.models.user import User
from app.schemas.transformation import TransformationCreate
from app.core.exceptions import NotFoundException, InsufficientCreditsException


class TransformationService:
    """Business logic for transformations"""

    @staticmethod
    def create_transformation(
        db: Session,
        user: Optional[User],
        transformation_data: TransformationCreate,
        original_image_url: str,
        reference_image_urls: List[str] = None
    ) -> Transformation:
        """
        Create a new transformation record

        Args:
            db: Database session
            user: User (optional for anonymous usage)
            transformation_data: Transformation parameters
            original_image_url: S3 URL of original image
            reference_image_urls: List of reference image URLs

        Returns:
            Created Transformation object
        """
        # Check user credits if authenticated
        if user:
            if user.credits <= 0:
                raise InsufficientCreditsException(
                    "Insufficient credits. Please upgrade your plan."
                )

        # Create transformation
        transformation = Transformation(
            user_id=user.id if user else None,
            job_id=str(uuid.uuid4()),
            status=TransformationStatus.PENDING,
            original_image_url=original_image_url,
            vibe=transformation_data.vibe,
            colors=transformation_data.colors,
            description=transformation_data.description,
            metadata={}
        )

        db.add(transformation)
        db.flush()  # Get the transformation.id

        # Add reference images
        if reference_image_urls:
            for ref_url in reference_image_urls:
                ref_image = ReferenceImage(
                    transformation_id=transformation.id,
                    image_url=ref_url,
                    image_type="reference"
                )
                db.add(ref_image)

        # Deduct credit from user
        if user:
            user.credits -= 1

        db.commit()
        db.refresh(transformation)

        return transformation

    @staticmethod
    def get_transformation_by_id(
        db: Session,
        transformation_id: uuid.UUID,
        user: Optional[User] = None
    ) -> Transformation:
        """Get transformation by ID"""
        query = db.query(Transformation).filter(Transformation.id == transformation_id)

        # If user is provided, ensure they own the transformation
        if user:
            query = query.filter(Transformation.user_id == user.id)

        transformation = query.first()

        if not transformation:
            raise NotFoundException("Transformation not found")

        return transformation

    @staticmethod
    def get_transformation_by_job_id(
        db: Session,
        job_id: str,
        user: Optional[User] = None
    ) -> Transformation:
        """Get transformation by job ID"""
        query = db.query(Transformation).filter(Transformation.job_id == job_id)

        # If user is provided, ensure they own the transformation
        if user:
            query = query.filter(Transformation.user_id == user.id)

        transformation = query.first()

        if not transformation:
            raise NotFoundException("Transformation not found")

        return transformation

    @staticmethod
    def get_user_transformations(
        db: Session,
        user: User,
        limit: int = 10,
        offset: int = 0
    ) -> tuple[List[Transformation], int]:
        """Get user's transformation history"""
        query = db.query(Transformation).filter(
            Transformation.user_id == user.id
        ).order_by(Transformation.created_at.desc())

        total = query.count()
        transformations = query.limit(limit).offset(offset).all()

        return transformations, total

    @staticmethod
    def delete_transformation(
        db: Session,
        transformation_id: uuid.UUID,
        user: User
    ) -> bool:
        """Delete a transformation"""
        transformation = TransformationService.get_transformation_by_id(
            db, transformation_id, user
        )

        db.delete(transformation)
        db.commit()
        return True
```

### 10.4 Auth Endpoints

```python
# app/api/v1/endpoints/auth.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.user import UserCreate, UserResponse
from app.schemas.auth import Token, LoginRequest, RefreshTokenRequest
from app.services.auth_service import AuthService
from app.core.exceptions import UnauthorizedException

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """Register a new user"""
    try:
        user = AuthService.create_user(db, user_data)
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/login", response_model=Token)
def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """Login and get access token"""
    user = AuthService.authenticate_user(db, login_data.email, login_data.password)

    if not user:
        raise UnauthorizedException("Incorrect email or password")

    tokens = AuthService.create_tokens(user.id)
    return tokens


@router.post("/refresh", response_model=Token)
def refresh_token(
    refresh_data: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """Refresh access token"""
    user = AuthService.get_user_from_token(db, refresh_data.refresh_token)

    if not user:
        raise UnauthorizedException("Invalid refresh token")

    tokens = AuthService.create_tokens(user.id)
    return tokens
```

### 10.5 Transformation Endpoints

```python
# app/api/v1/endpoints/transform.py

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, List
import uuid

from app.db.session import get_db
from app.dependencies import get_current_user, get_optional_user
from app.models.user import User
from app.schemas.transformation import (
    TransformationResponse,
    TransformationStatusResponse,
    TransformationListResponse
)
from app.services.transformation_service import TransformationService
from app.services.s3_service import s3_service
from app.utils.image_processor import ImageProcessor
from app.tasks.transformation_tasks import process_transformation
from app.core.exceptions import ValidationException

router = APIRouter()


@router.post("/transform", response_model=TransformationStatusResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_transformation(
    image: UploadFile = File(..., description="Room image to transform"),
    vibe: str = Form(..., description="Design vibe (modern, minimalist, etc.)"),
    colors: str = Form(..., description="Color palette (neutral, warm, etc.)"),
    description: Optional[str] = Form(None, description="Additional description"),
    reference_images: Optional[List[UploadFile]] = File(None, description="Reference images"),
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_optional_user)
):
    """
    Create a new interior transformation

    This endpoint:
    1. Uploads the original image to S3
    2. Optionally uploads reference images
    3. Creates a transformation record
    4. Queues a background job to process the transformation
    5. Returns immediately with job ID
    """
    try:
        # Read and validate image
        image_content = await image.read()
        ImageProcessor.validate_image(image_content, image.filename)

        # Sanitize image (remove EXIF)
        sanitized_content = ImageProcessor.sanitize_image(image_content)

        # Upload to S3
        from io import BytesIO
        original_url = s3_service.upload_file(
            file=BytesIO(sanitized_content),
            folder="originals",
            content_type=image.content_type
        )

        # Handle reference images
        reference_urls = []
        if reference_images:
            for ref_image in reference_images[:6]:  # Max 6 references
                ref_content = await ref_image.read()
                ImageProcessor.validate_image(ref_content, ref_image.filename)
                ref_sanitized = ImageProcessor.sanitize_image(ref_content)

                ref_url = s3_service.upload_file(
                    file=BytesIO(ref_sanitized),
                    folder="references",
                    content_type=ref_image.content_type
                )
                reference_urls.append(ref_url)

        # Create transformation record
        from app.schemas.transformation import TransformationCreate
        transformation_data = TransformationCreate(
            vibe=vibe,
            colors=colors,
            description=description
        )

        transformation = TransformationService.create_transformation(
            db=db,
            user=user,
            transformation_data=transformation_data,
            original_image_url=original_url,
            reference_image_urls=reference_urls
        )

        # Queue background job
        process_transformation.delay(
            transformation_id=str(transformation.id),
            original_image_url=original_url,
            vibe=vibe,
            colors=colors,
            description=description,
            reference_image_count=len(reference_urls)
        )

        return TransformationStatusResponse(
            job_id=transformation.job_id,
            status=transformation.status.value,
            original_url=original_url,
            transformed_url=None,
            processing_time=None,
            created_at=transformation.created_at,
            completed_at=None,
            metadata={
                "vibe": vibe,
                "colors": colors,
                "reference_count": len(reference_urls)
            }
        )

    except ValidationException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process transformation: {str(e)}"
        )


@router.get("/transform/{job_id}", response_model=TransformationStatusResponse)
def get_transformation_status(
    job_id: str,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_optional_user)
):
    """Get transformation status by job ID"""
    transformation = TransformationService.get_transformation_by_job_id(
        db=db,
        job_id=job_id,
        user=user
    )

    return TransformationStatusResponse(
        job_id=transformation.job_id,
        status=transformation.status.value,
        original_url=transformation.original_image_url,
        transformed_url=transformation.transformed_image_url,
        processing_time=transformation.processing_time_seconds,
        created_at=transformation.created_at,
        completed_at=transformation.completed_at,
        metadata={
            "vibe": transformation.vibe,
            "colors": transformation.colors,
            "description": transformation.description
        }
    )


@router.get("/history", response_model=TransformationListResponse)
def get_transformation_history(
    limit: int = 10,
    offset: int = 0,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Get user's transformation history"""
    transformations, total = TransformationService.get_user_transformations(
        db=db,
        user=user,
        limit=limit,
        offset=offset
    )

    return TransformationListResponse(
        transformations=transformations,
        total=total,
        limit=limit,
        offset=offset
    )


@router.delete("/transform/{transformation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transformation(
    transformation_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Delete a transformation"""
    TransformationService.delete_transformation(db, transformation_id, user)
    return None
```

### 10.6 User Endpoints

```python
# app/api/v1/endpoints/user.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.user import UserResponse

router = APIRouter()


@router.get("/me", response_model=UserResponse)
def get_current_user_info(
    user: User = Depends(get_current_user)
):
    """Get current user information"""
    return user


@router.get("/credits")
def get_user_credits(
    user: User = Depends(get_current_user)
):
    """Get user's remaining credits"""
    return {
        "credits": user.credits,
        "subscription_tier": user.subscription_tier.value
    }
```

### 10.7 Health Check Endpoint

```python
# app/api/v1/endpoints/health.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
import redis

from app.db.session import get_db
from app.core.config import settings

router = APIRouter()


@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint

    Checks:
    - Database connectivity
    - Redis connectivity
    - API responsiveness
    """
    health_status = {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "checks": {}
    }

    # Check database
    try:
        db.execute(text("SELECT 1"))
        health_status["checks"]["database"] = "healthy"
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["checks"]["database"] = f"unhealthy: {str(e)}"

    # Check Redis
    try:
        r = redis.from_url(settings.REDIS_URL)
        r.ping()
        health_status["checks"]["redis"] = "healthy"
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["checks"]["redis"] = f"unhealthy: {str(e)}"

    return health_status
```

### 10.8 API Router Aggregation

```python
# app/api/v1/api.py

from fastapi import APIRouter

from app.api.v1.endpoints import auth, transform, user, health

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(transform.router, prefix="/transform", tags=["transform"])
api_router.include_router(user.router, prefix="/user", tags=["user"])
api_router.include_router(health.router, tags=["health"])
```

---

**This is Part 2 of the Implementation Guide.**

**Continue to IMPLEMENTATION_GUIDE_PART3.md for:**
- Real-time Updates (Server-Sent Events)
- Rate Limiting
- Error Handling & Logging
- Testing
- Docker & Deployment
- CI/CD Pipeline

Would you like me to create Part 3 now, or shall I proceed directly to implementing the complete backend code?
