from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from domains import domain_shipping
from app.infra.deps import get_db
from schemas.shipping_schema import Shipping, ShippingCalc

shipping = APIRouter(
    prefix='/freight',
    tags=['freight'],
)

# @shipping.post('/zip_code/shipping', status_code= 200)
# def zip_code_shipping(shipping = Shipping):


@shipping.post('/zip_code/adress', status_code=200)
def zip_code_adress(shipping_data: Shipping) -> None:
    """Zip code adress."""
    return domain_shipping.adress_zip_code(shipping=shipping_data)


@shipping.post('/zip_code/shipping/calc', status_code=200)
def zip_code_shipping(
    *,
    db: Session = Depends(get_db),
    shipping_data: ShippingCalc,
) -> None:
    """Zip code shipping."""
    from loguru import logger

    logger.debug(shipping_data)
    return domain_shipping.shipping_zip_code(
        db=db,
        shipping_data=shipping_data,
    )
