from config import settings
from loguru import logger
from sqlalchemy.orm import Session

from app.infra.models.order import Product
from schemas.shipping_schema import Shipping, ShippingCalc
from zipcode.zip_code import CalculateShipping, FindZipCode


def shipping_zip_code(db: Session, shipping_data: ShippingCalc):
    try:
        _shipping_data = shipping_data.dict()
        if len(_shipping_data['shipping']) != 8:
            """ "Return -2 because shipping format error"""
            return {'shipping': -2}
        _product_id = _shipping_data['cart'][0]['product_id']
        _product = db.query(Product).filter_by(id=int(_product_id)).all()
        for _products in _shipping_data.get('cart'):
            _height = 0
            _weight = 0
            _width = 0
            _length = 0
            for product in _product:
                _height += product.heigth if product.heigth else 1
                _weight += product.weigth if product.weigth else 1
                _width += product.width if product.width else 1
                _length += product.length if product.length else 1

            _height = 1 if _height < 1 else _height
            _height = 99 if _height > 99 else _height

            _weight = 29 if _weight > 29 else _weight

            _width = 10 if _width < 10 else _width
            _width = 99 if _width > 99 else _width

            _length = 15 if _length < 15 else _length
            _length = 99 if _length > 99 else _length

            shipping = CalculateShipping(
                zip_code_source=str(settings.ZIP_CODE_SOURCE),
                zip_code_target=shipping_data.shipping,
                weigth=str(_weight),
                length=str(_length),
                heigth=str(_height),
                width=str(_width),
            )
            shipping = shipping.calculate_shipping()
            logger.debug(f'SHPPING RESULT {shipping} ')
            if shipping == []:
                return {'shipping': -2}
            return {'shipping': shipping}
    except Exception:
        logger.error('Erro no calculo do frete {e}')
        return {'shipping': -2}


def adress_zip_code(shipping: Shipping, status_code=200):
    try:
        adress = FindZipCode(zip_code_target=shipping.zip_code_target)
        return adress.find_zip_code_target()
    except Exception as e:
        raise e
