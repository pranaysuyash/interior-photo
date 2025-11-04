from celery import Task
from sqlalchemy.orm import Session
import time
import httpx
from datetime import datetime
from typing import Optional

from app.tasks.celery_app import celery_app
from app.db.session import SessionLocal
from app.models.transformation import Transformation, TransformationStatus
from app.core.config import settings
import replicate
import boto3
from io import BytesIO


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


def build_prompt(vibe: str, colors: str, description: Optional[str] = None) -> tuple[str, str]:
    """Build AI prompts"""
    vibe_prompts = {
        "modern": "contemporary, clean lines, sleek furniture, minimalist decor",
        "minimalist": "simple, uncluttered, neutral palette, essential furniture only",
        "cozy": "warm, comfortable, inviting, soft textures, ambient lighting",
        "industrial": "exposed brick, metal elements, concrete, Edison bulbs, loft style",
        "bohemian": "eclectic, colorful textiles, plants, vintage pieces",
        "scandinavian": "light wood, white walls, natural materials, hygge, functional",
        "luxurious": "elegant, high-end materials, chandeliers, plush furniture",
        "rustic": "wood beams, natural stone, vintage furniture, farmhouse style"
    }

    color_prompts = {
        "neutral": "beige, white, gray, cream, taupe color scheme",
        "warm": "terracotta, amber, rust, golden tones",
        "cool": "blue, teal, mint, cool gray tones",
        "earthy": "brown, olive green, terracotta, natural wood tones",
        "pastel": "soft pink, lavender, mint, baby blue, muted colors",
        "bold": "vibrant colors, deep jewel tones, saturated hues"
    }

    prompt_parts = [
        f"A {vibe} interior design,",
        vibe_prompts.get(vibe, "beautiful interior design"),
        f"with {color_prompts.get(colors, 'balanced color scheme')},",
        "photorealistic, high quality, professional photography, 8k resolution"
    ]

    if description:
        prompt_parts.insert(3, description)

    positive_prompt = " ".join(prompt_parts)
    negative_prompt = "ugly, distorted, low quality, blurry, pixelated, unrealistic"

    return positive_prompt, negative_prompt


@celery_app.task(bind=True, base=DatabaseTask, max_retries=3)
def process_transformation(
    self,
    transformation_id: str,
    original_image_url: str,
    vibe: str,
    colors: str,
    description: Optional[str] = None,
    reference_image_count: int = 0
):
    """Process interior transformation in background"""
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
        positive_prompt, negative_prompt = build_prompt(vibe, colors, description)

        # Call Replicate API
        output = replicate.run(
            settings.REPLICATE_MODEL,
            input={
                "image": original_image_url,
                "prompt": positive_prompt,
                "negative_prompt": negative_prompt,
                "num_inference_steps": 50,
                "guidance_scale": 7.5
            }
        )

        # Get result URL
        if isinstance(output, list) and len(output) > 0:
            transformed_url_temp = output[0]
        elif isinstance(output, str):
            transformed_url_temp = output
        else:
            raise ValueError(f"Unexpected output from Replicate: {output}")

        # Download transformed image from Replicate
        response = httpx.get(transformed_url_temp)
        response.raise_for_status()

        # Upload to our S3
        s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )

        import uuid
        filename = f"{uuid.uuid4()}.jpg"
        now = datetime.utcnow()
        key = f"transformed/{now.year}/{now.month:02d}/{now.day:02d}/{filename}"

        s3_client.put_object(
            Bucket=settings.S3_BUCKET_NAME,
            Key=key,
            Body=response.content,
            ContentType="image/jpeg"
        )

        final_url = f"{settings.CLOUDFRONT_URL or settings.S3_BUCKET_URL}/{key}"

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
            countdown = 2 ** self.request.retries
            raise self.retry(exc=exc, countdown=countdown)
        else:
            return {
                "status": "failed",
                "transformation_id": str(transformation_id),
                "error": str(exc)
            }
