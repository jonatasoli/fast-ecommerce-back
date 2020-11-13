from sqlalchemy.orm import backref, relationship
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
from sqlalchemy.types import JSON
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.types import Numeric
from passlib.hash import pbkdf2_sha512

from constants import DocumentType
from ext.database import Base

class Product(Base):
    id = Column(Integer, nullable=False, primary_key=True)
    name = Column(String)
    uri = Column(String)
    price = Column(Integer)
    active = Column(Boolean, default=True, server_default='0')
    direct_sales = Column(Boolean, default=False)
    upsell = Column(ARRAY(Integer), nullable=True)
    description = Column(String)
    image_path = Column(String)
    installments_config = Column(Integer, nullable=True)
    installments_list = Column(ARRAY(JSON), nullable=True)


class Cupons(Base):
    id = Column(Integer, nullable=False, primary_key=True)
    cupon_uuid = Column(String)
    cupon_name = Column(String)
    cupon_fee = Column(Numeric(10,2))
    qty = Column(Integer)
    active = Column(Boolean)


class Order(Base):
    id = Column(Integer, nullable=False, primary_key=True)
    customer_id = Column(Integer, ForeignKey("user.id"))
    order_date = Column(DateTime)
    tracking_number = Column(Integer, nullable=True)
    payment_id = Column(Integer, nullable=True)


class OrderItems(Base):
    id = Column(Integer, nullable=False, primary_key=True)
    order_id = Column(Integer, ForeignKey("order.id"))
    order = relationship("Order", backref=backref("order_items", uselist=False), cascade="all,delete", foreign_keys=[order_id])
    product_id = Column(Integer, ForeignKey("product.id"))
    product = relationship("Product", backref=backref("product", uselist=False), cascade="all,delete", foreign_keys=[product_id])
    quantity = Column(Integer)


class OrderStatusSteps(Base):
    id = Column(Integer, nullable=False, primary_key=True)
    order_id = Column(Integer)
    status = Column(String)
    last_updated = Column(DateTime)
    sending = Column(Boolean)
    active = Column(Boolean)

