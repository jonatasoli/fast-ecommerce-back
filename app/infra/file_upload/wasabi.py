import boto3
from fastapi import UploadFile
from config import settings
from boto3.exceptions import S3UploadFailedError
from loguru import logger


def upload_image(image: UploadFile, file_path) -> None:
    """Send image to wasabi."""
    try:
        s3 = boto3.client(
            's3',
            endpoint_url=f'{settings.ENDPOINT_UPLOAD_CLIENT}',
            aws_access_key_id=f'{settings.AWS_ACCESS_KEY_ID}',
            aws_secret_access_key=f'{settings.AWS_SECRET_ACCESS_KEY}',
        )

        if not file_path:
            file_path = image.filename
        s3.upload_file(
            f'{file_path}',
            f'{settings.BUCKET_NAME}',
            f'{settings.ENVIRONMENT}/{image.filename}',
            ExtraArgs={'ACL': 'public-read'},
        )
    except S3UploadFailedError:
        logger.info(s3)
        raise
