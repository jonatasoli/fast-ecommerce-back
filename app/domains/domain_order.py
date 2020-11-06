from sqlalchemy.orm import Session
from loguru import logger

from schemas.order_schema import ProductSchema, OrderSchema, ConfigOrder, ConfigUser

from models.order import Product, Order, OrderItems
from models.users import User
import json

def get_product(db : Session, uri):
    return db.query(Product).filter(Product.uri == uri).first()


def create_product(db: Session, product_data: ProductSchema):
    db_product = Product(**product_data.dict())
    db.add(db_product)
    db.commit()
    return db_product

def get_order(db: Session, id):
    order = db.query(Order).join(User).filter(Order.id == id).first()
    user = db.query(User.name).join(Order).first()
    output2 = ConfigOrder.from_orm(order)
    output1 = ConfigUser.from_orm(user)
    return (output1,output2)
    

def get_order_users(db: Session, id):
    order = db.query.with_entities((User.name).outerjoin(Order).filter(Order.customer_id == id)).all()
    dict1 = json.loads(order)
    return dict1

def crate_order():
    pass








