import enum
from fastapi import UploadFile
from config import settings
from PIL import Image, UnidentifiedImageError
from app.infra.file_upload import wasabi, spaces


class FileUploadClients(enum.Enum):
    WASABI = wasabi
    SPACES = spaces
    BUNNNY = NotImplementedError

class FileUploadBucketError(Exception):
    ...


def optimize_image(image: UploadFile) -> str:
    """Optimize images."""
    try:
        img = Image.open(image.file)
        if settings.ENVIRONMENT == 'development':
            img.save(f'./static/images/{image.filename}')
            return f'{settings.FILE_UPLOAD_PATH}{image.filename}'
        img.save(f'{image.filename}')
        _upload_file(image)
    except UnidentifiedImageError as err:
        raise FileUploadBucketError from err
    else:
        return (
            f'{settings.FILE_UPLOAD_PATH}{settings.ENVIRONMENT}/{image.filename}'
        )


def upload_video(video: UploadFile) -> str:
    """Upload video."""
    vdo = Image.open(video.file)
    if settings.ENVIRONMENT == 'development':
        vdo.save(f'./static/videos/{video.filename}')
        return f'{settings.FILE_UPLOAD_PATH}{video.filename}'
    vdo.save(f'{video.filename}')
    _upload_file(video)
    return (
        f'{settings.FILE_UPLOAD_PATH}{settings.ENVIRONMENT}/{video.filename}'
    )


def _upload_file(image: UploadFile) -> None:
    """Select client and send image."""
    client = FileUploadClients[f'{settings.FILE_UPLOAD_CLIENT}'].value
    client.upload_image(image)
