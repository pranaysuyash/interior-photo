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

        # Convert to RGB if necessary
        if image.mode in ('RGBA', 'LA', 'P'):
            # Create white background
            background = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'RGBA':
                background.paste(image, mask=image.split()[3])  # Alpha channel
            else:
                background.paste(image)
            image = background

        # Remove EXIF data by getting raw pixel data
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

    @staticmethod
    def resize_image(file_content: bytes, max_size: Tuple[int, int] = (2048, 2048)) -> bytes:
        """
        Resize image if larger than max_size

        Args:
            file_content: Original image content
            max_size: Maximum dimensions (width, height)

        Returns:
            Resized image content
        """
        image = Image.open(BytesIO(file_content))

        # Convert to RGB if necessary
        if image.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'RGBA':
                background.paste(image, mask=image.split()[3])
            else:
                background.paste(image)
            image = background

        # Resize if needed
        if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
            image.thumbnail(max_size, Image.Resampling.LANCZOS)

        # Save to bytes
        output = BytesIO()
        image.save(output, format='JPEG', quality=85, optimize=True)
        return output.getvalue()
