import boto3
from fastapi import UploadFile
from config import settings


def upload_image(image: UploadFile) -> None:
    """Send image to wasabi."""
    # Create connection to Wasabi / S3
    s3 = boto3.resource(
        's3',
        endpoint_url=f'{settings.ENDPOINT_UPLOAD_CLIENT}',
        aws_access_key_id=f'{settings.AWS_ACCESS_KEY_ID}',
        aws_secret_access_key=f'{settings.AWS_SECRET_ACCESS_KEY}',
    )

    # Get bucket object
    boto_test_bucket = s3.Bucket(f'{settings.BUCKET_NAME}')

    # Upload the file. "MyDirectory/test.txt" is the name of the object to create
    boto_test_bucket.upload_file(
        f'{image.filename}',
        f'{settings.ENVIRONMENT}/{image.filename}',
    )
