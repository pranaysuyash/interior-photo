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
