from sqlalchemy.orm import Session
from loguru import logger
from ext.database import SessionLocal

from schemas.order_schema import ProductSchema

from models.order import Product

def get_product(uri):
    db = SessionLocal()
    return db.query(Product).filter(Product.uri == uri).first()


def create_product(db: Session, product_data: ProductSchema):
    db_product = Product(**product_data.dict())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

