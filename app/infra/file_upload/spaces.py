import boto3
from config import settings
from fastapi import UploadFile


def upload_image(image: UploadFile) -> None:
    """Send image to digital ocean spaces."""
    client = boto3.resource(
        's3',
        region_name=f'{settings.ENDPOINT_UPLOAD_REGION}',
        endpoint_url=f'{settings.ENDPOINT_UPLOAD_CLIENT}',
        aws_access_key_id=settings.AWS_ACESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    )

    client.upload_file(
        f'{image.filename}',
        f'{settings.BUCKET_NAME}',
        f'{image.filename}',
        ExtraArgs={'ACL': 'public-read'},
    )
