from fastapi import Header, APIRouter, Depends
from sqlalchemy.orm import Session
from schemas.shipping_schema import Shipping
from domains import domain_shipping 
from endpoints.deps import get_db

shipping = APIRouter()

@shipping.post('/zip_code/shipping', status_code= 200)
def zip_code_shipping(shipping_data: Shipping):
    shipping = domain_shipping.shipping_zip_code(shipping=shipping_data)
    return shipping

@shipping.post('/zip_code/adress', status_code=200)
def zip_code_adress(shipping_data: Shipping):
    adress = domain_shipping.adress_zip_code(shipping=shipping_data)
    return adress