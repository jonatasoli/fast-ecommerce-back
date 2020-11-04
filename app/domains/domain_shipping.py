from schemas.shipping_schema import Shipping
from zipcode.zip_code import CalculateShipping, FindZipCode
from dynaconf import settings

def shipping_zip_code(shipping: Shipping):
    try: 
        shipping = CalculateShipping(
            zip_code_source=settings.ZIP_CODE_SOURCE,
            zip_code_target=shipping.zip_code_target,
            weigth=shipping.weigth,
            length=shipping.length,
            heigth=shipping.heigth,
            width=shipping.width,
            diameter=shipping.diameter
        )
        shipping = shipping.calculate_shipping()
        return shipping
    except Exception as e:
        raise e

def adress_zip_code(shipping: Shipping, status_code=200):
    try:
        adress = FindZipCode(zip_code_target=shipping.zip_code_target)
        adress = adress.find_zip_code_target()
        return adress
    except Exception as e:
        raise e
    
    
 