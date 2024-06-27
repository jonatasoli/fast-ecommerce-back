from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal
from app.entities.product import ProductInDB


class MetricError(Exception):
    ...


MAX_WEIGHT = 30
MAX_LENGTH = 105
MAX_WIDTH = 105
MAX_HEIGHT = 105
MAX_DIAMETER = 91
MIN_LENGTH = 16
MIN_WIDTH = 11
MIN_HEIGHT = 2


def raise_metric_error():
    """Raise metric freight error."""
    raise MetricError


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
        _metric = (
            product.length * product.width
            if product.width > 0
            else product.diameter
        )
        if not _metric:
            raise raise_metric_error()
        volume += product.height * _metric

    _lenght = _width = _height = int(volume) ** (1 / 3)
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

class ShippingAddress(BaseModel):
    ship_name: str | None = None
    ship_address: str | None = None
    ship_number: str | None = None
    ship_address_complement: str | None = None
    ship_neighborhood: str | None = None
    ship_city: str | None = None
    ship_state: str | None = None
    ship_country: str | None = None
    ship_zip: str | None = None


class TrackingFullResponse(BaseModel):
    tracking_number: str
