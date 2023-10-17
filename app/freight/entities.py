from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel
from app.entities.product import ProductInDB


MAX_WEIGHT = 30
MAX_LENGTH = 105
MAX_WIDTH = 105
MAX_HEIGHT = 105
MAX_DIAMETER = 91
MIN_LENGTH = 16
MIN_WIDTH = 11
MIN_HEIGHT = 2


class FreightPackage(BaseModel):
    weight: str
    length: str
    height: str
    width: str


class Freight(BaseModel):
    price: Decimal
    delivery_time: int
    max_date: datetime


def calculate_package(products: list[ProductInDB]) -> FreightPackage:
    """Calculate package weight and volume."""
    weight, volume = 0, 0
    for product in products:
        weight += product.weight
        volume += product.length * product.height * product.width

    _lenght = _width = _height = volume ** (1 / 3)
    if _lenght <= MIN_LENGTH:
        _lenght = MIN_LENGTH
    elif _lenght >= MAX_LENGTH:
        _lenght = MAX_LENGTH

    if _width <= MIN_WIDTH:
        _width = MIN_WIDTH
    elif _width >= MAX_WIDTH:
        _width = MAX_WIDTH

    if _height <= MIN_HEIGHT:
        _height = MIN_HEIGHT
    elif _height >= MAX_HEIGHT:
        _height = MAX_HEIGHT

    return FreightPackage(
        weight=str(weight),
        length=str(_lenght),
        height=str(_height),
        width=str(_width),
    )
