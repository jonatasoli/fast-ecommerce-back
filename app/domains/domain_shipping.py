from sqlalchemy.orm import Session
from schemas.shipping_schema import Shipping, ShippingCalc
from schemas.order_schema import CheckoutSchema
from models.order import Product
from zipcode.zip_code import CalculateShipping, FindZipCode
from dynaconf import settings

from loguru import logger

def shipping_zip_code(db: Session, shipping_data: ShippingCalc):
    _shipping_data = shipping_data.dict()
    _product_id = _shipping_data['cart'][0]['product_id']
    _product = db.query(Product).filter_by(id=int(_product_id)).all()
    for products in _shipping_data.get('cart'):
        for product in _product:
            product ={
                "heigth":product.heigth, 
                "weigth":product.weigth, 
                "width":product.width, 
                "depthe":product.depthe} 
    
        shipping = CalculateShipping(
                zip_code_source=str(settings.ZIP_CODE_SOURCE),
                zip_code_target=shipping_data.shipping,
                weigth=str(product.get('weigth')),
                length=str(product.get('depthe')),
                heigth=str(product.get('heigth')),
                width=str(product.get('width'))
            )
        shipping = shipping.calculate_shipping()
        logger.debug(shipping)
        shipping = next(shipping)
        return {"shipping": int((shipping['frete'].replace(",", "")))} 


def adress_zip_code(shipping: Shipping, status_code=200):
    try:
        adress = FindZipCode(zip_code_target=shipping.zip_code_target)
        adress = adress.find_zip_code_target()
        return adress
    except Exception as e:
        raise e
    
    
 
