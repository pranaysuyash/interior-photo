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


class ReferenceImage(Base):
    __tablename__ = "reference_images"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transformation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("transformations.id", ondelete="CASCADE"),
        nullable=False
    )
    image_url = Column(Text, nullable=False)
    image_type = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)

    transformation = relationship("Transformation", back_populates="reference_images")

    def __repr__(self):
        return f"<ReferenceImage {self.id}>"
