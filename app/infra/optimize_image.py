from dynaconf import settings
from PIL import Image

from app.infra.spaces import send_image_spaces


def optimize_image(image: str) -> None:
    """Optimize images."""
    img = Image.open(image.file)
    if settings.ENVIRONMENT == 'development':
        img.save(f'./static/images/{image.filename}')
        return f'http://localhost:7777/static/images/{image.filename}'
    img.save(f'{image.filename}')
    send_image_spaces(image.filename)
    return f'https://gattorosa.nyc3.digitaloceanspaces.com/{image.filename}'
