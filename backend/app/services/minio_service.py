from minio import Minio
from minio.error import S3Error
import logging
import json
from ..core.config import settings
from io import BytesIO

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MinioService:
    def __init__(self):
        # Use internal URL for Docker communication
        # The Minio client expects just 'host:port', not 'http://host:port'
        # Determine if we should use secure connection based on original URL scheme
        secure_connection = settings.MINIO_INTERNAL_URL.startswith("https://")
        minio_internal_url = settings.MINIO_INTERNAL_URL.replace("http://", "").replace("https://", "")
        self.client = Minio(
            minio_internal_url,
            access_key=settings.MINIO_ROOT_USER,
            secret_key=settings.MINIO_ROOT_PASSWORD,
            secure=secure_connection
        )

    def _ensure_bucket_exists(self, bucket_name: str):
        try:
            found = self.client.bucket_exists(bucket_name)
            if not found:
                self.client.make_bucket(bucket_name)
                logger.info(f"Bucket '{bucket_name}' created.")
                
                # Set a public read-only policy on the bucket
                policy = {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Principal": {"AWS": "*"},
                            "Action": ["s3:GetObject"],
                            "Resource": [f"arn:aws:s3:::{bucket_name}/*"],
                        },
                    ],
                }
                self.client.set_bucket_policy(bucket_name, json.dumps(policy))
                logger.info(f"Public read policy set for bucket '{bucket_name}'.")
        except S3Error as e:
            logger.error(f"Error checking or creating bucket: {e}")
            raise

    def upload_file(self, bucket_name: str, file_name: str, file_data: bytes, content_type: str) -> str:
        self._ensure_bucket_exists(bucket_name)
        try:
            file_stream = BytesIO(file_data)
            file_size = len(file_data)

            self.client.put_object(
                bucket_name=bucket_name,
                object_name=file_name,
                data=file_stream,
                length=file_size,
                content_type=content_type,
            )

            # Construct the public URL using the configured MINIO_PUBLIC_URL
            public_url = f"{settings.MINIO_PUBLIC_URL}/{bucket_name}/{file_name}"
            logger.info(f"File '{file_name}' uploaded to bucket '{bucket_name}'. URL: {public_url}")
            return public_url
        except S3Error as e:
            logger.error(f"Error uploading file to MinIO: {e}")
            raise

    def list_objects(self, bucket_name: str):
        """List all objects in a bucket."""
        try:
            self._ensure_bucket_exists(bucket_name)
            objects = self.client.list_objects(bucket_name, recursive=True)
            return list(objects)
        except S3Error as e:
            logger.error(f"Error listing objects in bucket '{bucket_name}': {e}")
            raise

    def get_object_stat(self, bucket_name: str, object_name: str):
        """Get object metadata."""
        try:
            return self.client.stat_object(bucket_name, object_name)
        except S3Error as e:
            logger.error(f"Error getting object stat for '{object_name}': {e}")
            raise

    def get_public_url(self, bucket_name: str, object_name: str) -> str:
        """Generate public URL for an object."""
        return f"{settings.MINIO_PUBLIC_URL}/{bucket_name}/{object_name}"

    def delete_file(self, bucket_name: str, file_name: str) -> bool:
        """
        Delete a file from MinIO bucket.
        
        Args:
            bucket_name: Name of the bucket
            file_name: Name of the file to delete
            
        Returns:
            bool: True if deletion was successful, False otherwise
        """
        try:
            self.client.remove_object(bucket_name, file_name)
            logger.debug(f"Deleted '{file_name}' from bucket '{bucket_name}'")
            return True
        except S3Error as e:
            logger.error(f"Error deleting file '{file_name}' from bucket '{bucket_name}': {e}")
            return False

    def delete_file_by_url(self, file_url: str) -> bool:
        """
        Delete a file from MinIO using its public URL.
        
        Args:
            file_url: Full public URL of the file (e.g., https://domain/bucket/file.png)
            
        Returns:
            bool: True if deletion was successful, False otherwise
        """
        try:
            # Extract bucket and filename from URL
            # Expected format: {MINIO_PUBLIC_URL}/{bucket_name}/{file_name}
            if not file_url.startswith(settings.MINIO_PUBLIC_URL):
                logger.debug(f"Skipping non-MinIO URL: {file_url}")
                return False
            
            # Remove the base URL and split into bucket/filename
            path = file_url.replace(settings.MINIO_PUBLIC_URL + "/", "")
            parts = path.split("/", 1)
            
            if len(parts) != 2:
                logger.warning(f"Could not parse bucket and filename from URL: {file_url}")
                return False
            
            bucket_name, file_name = parts
            return self.delete_file(bucket_name, file_name)
            
        except Exception as e:
            logger.error(f"Error parsing or deleting file from URL '{file_url}': {e}")
            return False

minio_service = MinioService() 