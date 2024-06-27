from pydantic import BaseModel
from app.entities.product import ProductInDB

from app.entities.freight import Freight, FreightPackage, calculate_package
from app.infra.freight.correios_br import (
    PACKAGE_TYPE,
    DeliveryPriceParams,
    calculate_delivery_time,
    calculate_delivery_price,
)
from config import settings


class FreightCart(BaseModel):
    """Freight cart."""

    volume: float
    weight: float


def calculate_volume_weight(
    products: list[ProductInDB],
) -> FreightPackage:
    """Get freight from zip code."""
    return calculate_package(products)


def get_freight(
    product_code: str,
    *,
    freight_package: FreightPackage,
    zipcode: str,
) -> Freight:
    """Get freight from zip code."""
    package_delivery = calculate_delivery_time(
        zipcode,
        product_code=product_code,
    )
    package_price_params = DeliveryPriceParams(
        psObjeto=freight_package.weight,
        comprimento=freight_package.length,
        largura=freight_package.width,
        altura=freight_package.height,
        cepOrigem=str(settings.CORREIOSBR_CEP_ORIGIN),
        cepDestino=zipcode,
        tpObjeto=PACKAGE_TYPE,
    )
    price = calculate_delivery_price(
        product_code,
        package=package_price_params,
    )
    return Freight(
        price=price.price,
        delivery_time=package_delivery.delivery_time,
        max_date=package_delivery.max_date,
    )
