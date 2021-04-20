from PIL import Image
from dynaconf import settings
from loguru import  logger
from .spaces import send_image_spaces

def optimize_image(image):
    size = (300, 300)
    img = Image.open(image.file)
    img = img.resize(size)
    if settings.ENVIRONMENT == 'development': 
        img.save(f'./static/{image.filename}')
        return f'http://localhost:7777/static/{image.filename}'
    else:
        img.save(f'{image.filename}')
        send_image_spaces(image.filename)
        return f'https://gattorosa.nyc3.digitaloceanspaces.com/{image.filename}'