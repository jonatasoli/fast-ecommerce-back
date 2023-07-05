from passlib.hash import pbkdf2_sha512
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import backref, relationship
from sqlalchemy.types import JSON, Numeric

from constants import DocumentType
from ext.database import Base
from models.users import User


class Product(Base):
    id = Column(Integer, nullable=False, primary_key=True)
    name = Column(String)
    uri = Column(String)
    price = Column(Integer)
    active = Column(Boolean, default=True)
    direct_sales = Column(Boolean, default=False)
    upsell = Column(ARRAY(Integer), nullable=True)
    description = Column(String)
    image_path = Column(String)
    installments_config = Column(Integer, nullable=True)
    installments_list = Column(ARRAY(JSON), nullable=True)
    discount = Column(Integer, nullable=True)
    category_id = Column(Integer, ForeignKey('category.id'))
    category = relationship(
        'Category',
        foreign_keys=[category_id],
        backref='Product',
        cascade='all,delete',
        uselist=False,
    )
    showcase = Column(Boolean, default=True)
    show_discount = Column(Boolean, default=False)
    height = Column(Numeric(5, 3), nullable=True)
    width = Column(Numeric(5, 3), nullable=True)
    weight = Column(Numeric(5, 3), nullable=True)
    length = Column(Numeric(5, 3), nullable=True)
    diameter = Column(Numeric(5, 3), nullable=True)


class Cupons(Base):
    id = Column(Integer, nullable=False, primary_key=True)
    cupon_uuid = Column(String)
    cupon_name = Column(String)
    cupon_fee = Column(Numeric(10, 2))
    qty = Column(Integer)
    active = Column(Boolean)


class Coupons(Base):
    id = Column(Integer, nullable=False, primary_key=True)
    code = Column(String)
    discount = Column(Numeric(10, 2))
    qty = Column(Integer)
    active = Column(Boolean)


class Order(Base):
    id = Column(Integer, nullable=False, primary_key=True)
    customer_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(
        'User',
        foreign_keys=[customer_id],
        backref='Order',
        cascade='all,delete',
        uselist=False,
    )
    order_date = Column(DateTime)
    tracking_number = Column(String, nullable=True)
    payment_id = Column(Integer, nullable=True)
    order_status = Column(String)
    last_updated = Column(DateTime)
    checked = Column(Boolean, default=False)


class OrderItems(Base):
    id = Column(Integer, nullable=False, primary_key=True)
    order_id = Column(Integer, ForeignKey('order.id'))
    order = relationship(
        'Order',
        backref=backref('order_items', uselist=False),
        cascade='all,delete',
        foreign_keys=[order_id],
    )
    product_id = Column(Integer, ForeignKey('product.id'))
    product = relationship(
        'Product',
        backref=backref('product', uselist=False),
        cascade='all,delete',
        foreign_keys=[product_id],
    )
    quantity = Column(Integer)


class OrderStatusSteps(Base):
    id = Column(Integer, nullable=False, primary_key=True)
    order_id = Column(Integer)
    status = Column(String)
    last_updated = Column(DateTime)
    sending = Column(Boolean)
    active = Column(Boolean)


class Category(Base):
    id = Column(Integer, nullable=False, primary_key=True)
    name = Column(String)
    path = Column(String)


class ImageGallery(Base):
    id = Column(Integer, nullable=False, primary_key=True)
    url = Column(String)
    product_id = Column(Integer)
