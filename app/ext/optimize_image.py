from PIL import Image
from dynaconf import settings
from loguru import  logger
from .spaces import send_image_spaces

def optimize_image(image):
    size = (300, 300)
    img = Image.open(image.file)
    img = img.resize(size)
    img.save(f'./static/{image.filename}')
    if settings.ENVIRONMENT == 'development': 
        return f'http://localhost:7777/static/{image.filename}'
    else:
        send_image_spaces(image.filename)
        return f'https://fastecommerce.nyc3.digitaloceanspaces.com/{image.filename}'