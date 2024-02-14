import enum
from fastapi import UploadFile
from config import settings
from PIL import Image
from app.infra.file_upload import wasabi, spaces


class FileUploadClients(enum.Enum):
    WASABI = wasabi
    SPACES = spaces


def optimize_image(image: UploadFile) -> str:
    """Optimize images."""
    img = Image.open(image.file)
    if settings.ENVIRONMENT == 'development':
        img.save(f'./static/images/{image.filename}')
        return f'{settings.FILE_UPLOAD_PATH}{image.filename}'
    img.save(f'{image.filename}')
    _upload_file(image)
    return (
        f'{settings.FILE_UPLOAD_PATH}{settings.ENVIRONMENT}/{image.filename}'
    )


def _upload_file(image: UploadFile) -> None:
    """Select client and send image."""
    client = FileUploadClients['settings.FILE_UPLOAD_CLIENT'].value
    client.upload_image(image)
