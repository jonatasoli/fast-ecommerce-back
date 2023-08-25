import boto3
from dynaconf import settings


def send_image_spaces(image_name: str) -> None:
    """Send image to digital ocean spaces."""
    session = boto3.session.Session()
    client = session.client(
        's3',
        region_name='nyc3',
        endpoint_url='https://nyc3.digitaloceanspaces.com',
        aws_access_key_id=settings.AWS_ACESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    )

    client.upload_file(
        f'{image_name}',  # Path to local file
        'gattorosa',  # Name of Space
        f'{image_name}',
        ExtraArgs={'ACL': 'public-read'},
    )  # Name for remote file
