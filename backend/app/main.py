"""
Interior AI Backend - Main Application
Complete FastAPI application with authentication, transformations, and AI integration
"""

from fastapi import FastAPI, Depends, UploadFile, File, Form, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional, List
import logging
import uuid

from app.core.config import settings
from app.db.session import get_db

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

# Security
security = HTTPBearer()


# ============================================================================
# PYDANTIC SCHEMAS
# ============================================================================

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: Optional[str] = None


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    name: Optional[str]
    credits: int
    subscription_tier: str

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    email: str
    password: str


class TransformationStatusResponse(BaseModel):
    job_id: str
    status: str
    original_url: str
    transformed_url: Optional[str] = None
    processing_time: Optional[float] = None
    created_at: str
    completed_at: Optional[str] = None
    metadata: dict = {}


# ============================================================================
# AUTHENTICATION DEPENDENCIES
# ============================================================================

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Get current authenticated user"""
    from app.models.user import User
    from app.core.security import decode_token

    token = credentials.credentials
    payload = decode_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )

    user = db.query(User).filter(User.id == user_id).first()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )

    return user


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: Session = Depends(get_db)
):
    """Get current user if authenticated, None otherwise"""
    if not credentials:
        return None

    try:
        return await get_current_user(credentials, db)
    except:
        return None


# ============================================================================
# STARTUP/SHUTDOWN EVENTS
# ============================================================================

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


# ============================================================================
# ROOT & HEALTH CHECK ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs" if settings.DEBUG else "disabled in production"
    }


@app.get("/api/v1/health")
def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint
    Checks database and Redis connectivity
    """
    from sqlalchemy import text
    import redis

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


# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

@app.post("/api/v1/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """Register a new user"""
    from app.models.user import User
    from app.core.security import get_password_hash

    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create user
    user = User(
        email=user_data.email,
        name=user_data.name,
        password_hash=get_password_hash(user_data.password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.post("/api/v1/auth/login", response_model=Token)
def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """Login and get access token"""
    from app.models.user import User
    from app.core.security import verify_password, create_access_token, create_refresh_token

    user = db.query(User).filter(User.email == login_data.email).first()

    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


# ============================================================================
# USER ENDPOINTS
# ============================================================================

@app.get("/api/v1/user/me", response_model=UserResponse)
def get_current_user_info(
    current_user = Depends(get_current_user)
):
    """Get current user information"""
    return current_user


@app.get("/api/v1/user/credits")
def get_user_credits(
    current_user = Depends(get_current_user)
):
    """Get user's remaining credits"""
    return {
        "credits": current_user.credits,
        "subscription_tier": current_user.subscription_tier.value
    }


# ============================================================================
# TRANSFORMATION ENDPOINTS
# ============================================================================

@app.post("/api/v1/transform/transform", response_model=TransformationStatusResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_transformation(
    image: UploadFile = File(..., description="Room image to transform"),
    vibe: str = Form(..., description="Design vibe (modern, minimalist, etc.)"),
    colors: str = Form(..., description="Color palette (neutral, warm, etc.)"),
    description: Optional[str] = Form(None, description="Additional description"),
    db: Session = Depends(get_db),
    user = Depends(get_optional_user)
):
    """
    Create a new interior transformation

    This endpoint:
    1. Uploads the original image to S3
    2. Creates a transformation record
    3. Queues a background job to process the transformation
    4. Returns immediately with job ID
    """
    from app.models.transformation import Transformation, TransformationStatus
    from PIL import Image
    from io import BytesIO
    import boto3
    from datetime import datetime

    try:
        # Check user credits if authenticated
        if user and user.credits <= 0:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail="Insufficient credits"
            )

        # Read and validate image
        image_content = await image.read()

        # Validate size
        file_size_mb = len(image_content) / (1024 * 1024)
        if file_size_mb > settings.MAX_IMAGE_SIZE_MB:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Image size ({file_size_mb:.1f}MB) exceeds maximum ({settings.MAX_IMAGE_SIZE_MB}MB)"
            )

        # Validate image format
        try:
            img = Image.open(BytesIO(image_content))
            img.verify()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid image file: {str(e)}"
            )

        # Upload to S3 (simplified - in production use the S3Service)
        s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )

        # Generate filename
        filename = f"{uuid.uuid4()}.jpg"
        now = datetime.utcnow()
        key = f"originals/{now.year}/{now.month:02d}/{now.day:02d}/{filename}"

        # Upload
        s3_client.put_object(
            Bucket=settings.S3_BUCKET_NAME,
            Key=key,
            Body=image_content,
            ContentType="image/jpeg"
        )

        original_url = f"{settings.CLOUDFRONT_URL or settings.S3_BUCKET_URL}/{key}"

        # Create transformation record
        job_id = str(uuid.uuid4())
        transformation = Transformation(
            user_id=user.id if user else None,
            job_id=job_id,
            status=TransformationStatus.PENDING,
            original_image_url=original_url,
            vibe=vibe,
            colors=colors,
            description=description,
            metadata={}
        )

        db.add(transformation)

        # Deduct credit if user is authenticated
        if user:
            user.credits -= 1

        db.commit()
        db.refresh(transformation)

        # Queue background job (simplified - in production use Celery)
        # For now, just mark as pending and return
        try:
            from app.tasks.transformation_tasks import process_transformation
            process_transformation.delay(
                transformation_id=str(transformation.id),
                original_image_url=original_url,
                vibe=vibe,
                colors=colors,
                description=description,
                reference_image_count=0
            )
        except Exception as e:
            logger.warning(f"Could not queue task (Celery may not be running): {e}")

        return TransformationStatusResponse(
            job_id=transformation.job_id,
            status=transformation.status.value,
            original_url=original_url,
            transformed_url=None,
            processing_time=None,
            created_at=transformation.created_at.isoformat(),
            completed_at=None,
            metadata={
                "vibe": vibe,
                "colors": colors
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating transformation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process transformation: {str(e)}"
        )


@app.get("/api/v1/transform/{job_id}", response_model=TransformationStatusResponse)
def get_transformation_status(
    job_id: str,
    db: Session = Depends(get_db),
    user = Depends(get_optional_user)
):
    """Get transformation status by job ID"""
    from app.models.transformation import Transformation

    query = db.query(Transformation).filter(Transformation.job_id == job_id)

    # If user is provided, ensure they own the transformation
    if user:
        query = query.filter(Transformation.user_id == user.id)

    transformation = query.first()

    if not transformation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transformation not found"
        )

    return TransformationStatusResponse(
        job_id=transformation.job_id,
        status=transformation.status.value,
        original_url=transformation.original_image_url,
        transformed_url=transformation.transformed_image_url,
        processing_time=transformation.processing_time_seconds,
        created_at=transformation.created_at.isoformat(),
        completed_at=transformation.completed_at.isoformat() if transformation.completed_at else None,
        metadata={
            "vibe": transformation.vibe,
            "colors": transformation.colors,
            "description": transformation.description
        }
    )


@app.get("/api/v1/transform/history")
def get_transformation_history(
    limit: int = 10,
    offset: int = 0,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    """Get user's transformation history"""
    from app.models.transformation import Transformation

    query = db.query(Transformation).filter(
        Transformation.user_id == user.id
    ).order_by(Transformation.created_at.desc())

    total = query.count()
    transformations = query.limit(limit).offset(offset).all()

    return {
        "transformations": transformations,
        "total": total,
        "limit": limit,
        "offset": offset
    }


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="debug" if settings.DEBUG else "info"
    )
