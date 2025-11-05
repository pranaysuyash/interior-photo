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
