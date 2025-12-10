import enum
import io
import shutil
from pathlib import Path
from fastapi import UploadFile
from config import settings
from PIL import Image, UnidentifiedImageError
from app.infra.file_upload import wasabi, spaces


class FileUploadClients(enum.Enum):
    WASABI = wasabi
    SPACES = spaces
    BUNNNY = NotImplementedError


class FileUploadBucketError(Exception): ...


def optimize_image(image: UploadFile) -> str:
    """Optimize images and convert to WebP."""
    try:
        img = Image.open(image.file)

        if img.mode in ('RGBA', 'LA', 'P'):
            rgb_img = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            rgb_img.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
            img = rgb_img
        elif img.mode != 'RGB':
            img = img.convert('RGB')

        max_size = 1920
        if max(img.size) > max_size:
            ratio = max_size / max(img.size)
            new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
            img = img.resize(new_size, Image.Resampling.LANCZOS)

        original_name = Path(image.filename).stem if image.filename else 'image'
        webp_filename = f'{original_name}.webp'

        webp_buffer = io.BytesIO()
        img.save(webp_buffer, format='WEBP', quality=85, method=6)
        webp_buffer.seek(0)

        image.file = webp_buffer
        image.filename = webp_filename

        if settings.ENVIRONMENT == 'development':
            output_path = Path('./static/images') / webp_filename
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'wb') as f:
                f.write(webp_buffer.getvalue())
            return f'{settings.FILE_UPLOAD_PATH}{webp_filename}'

        _upload_file(image)
    except UnidentifiedImageError as err:
        raise FileUploadBucketError from err
    else:
        return f'{settings.FILE_UPLOAD_PATH}{settings.ENVIRONMENT}/{webp_filename}'


async def upload_video(video: UploadFile) -> str:
    """Upload video."""
    upload_dir = Path('./static/videos')
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / video.filename
    with open(file_path, 'wb') as vdo:
        vdo.write(await video.read())
        if settings.ENVIRONMENT == 'development':
            return f'{settings.FILE_UPLOAD_PATH}{video.filename}'
    _upload_file(video, file_path)
    return f'{settings.FILE_UPLOAD_PATH}{settings.ENVIRONMENT}/{video.filename}'


def _upload_file(image: UploadFile, file_path=None) -> None:
    """Select client and send image."""
    client = FileUploadClients[f'{settings.FILE_UPLOAD_CLIENT}'].value
    client.upload_image(image, file_path)
