from datetime import datetime
from decimal import Decimal
from pydantic import Json
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, backref, mapped_column, relationship
from sqlalchemy.types import JSON

from app.infra.models.base import Base


class Category(Base):
    __tablename__ = 'category'

    category_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    path: Mapped[str]
    menu: Mapped[bool] = mapped_column(default=False)
    showcase: Mapped[bool] = mapped_column(default=False)
    image_path: Mapped[str | None]


class Product(Base):
    __tablename__ = 'product'

    product_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    uri: Mapped[str]
    price: Mapped[Decimal]
    active: Mapped[bool] = mapped_column(default=False)
    direct_sales: Mapped[bool] = mapped_column(default=False)
    description: Mapped[Json] = mapped_column(JSON, nullable=True)
    image_path: Mapped[str | None]
    installments_config: Mapped[int]
    installments_list: Mapped[dict] = mapped_column(JSON, nullable=True)
    discount: Mapped[int | None]
    category_id: Mapped[int] = mapped_column(
        ForeignKey('category.category_id'),
    )
    category: Mapped['Category'] = relationship(
        foreign_keys=[category_id],
        backref='Product',
        cascade='all,delete',
        uselist=False,
        lazy='joined',
    )
    showcase: Mapped[bool] = mapped_column(default=False)
    feature: Mapped[bool] = mapped_column(default=False, server_default='0')
    show_discount: Mapped[bool] = mapped_column(default=False)
    height: Mapped[Decimal | None]
    width: Mapped[Decimal | None]
    weight: Mapped[Decimal | None]
    length: Mapped[Decimal | None]
    diameter: Mapped[Decimal | None]
    sku: Mapped[str]
    currency: Mapped[str] = mapped_column(default='BRL', default_server='BRL')


class Coupons(Base):
    __tablename__ = 'coupons'

    coupon_id: Mapped[int] = mapped_column(primary_key=True)
    affiliate_id: Mapped[int | None] = mapped_column(
        ForeignKey('user.user_id'),
    )
    user = relationship(
        'User',
        foreign_keys=[affiliate_id],
        backref='Coupons',
        cascade='all,delete',
        uselist=False,
    )
    code: Mapped[str]
    discount: Mapped[Decimal]
    qty: Mapped[int]
    active: Mapped[bool] = mapped_column(default=True)


class Order(Base):
    __tablename__ = 'order'

    order_id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('user.user_id'))
    user = relationship(
        'User',
        foreign_keys=[user_id],
        backref='Order',
        cascade='all,delete',
        uselist=False,
    )
    affiliate_id: Mapped[int | None]
    customer_id: Mapped[str]
    order_date: Mapped[datetime]
    cart_uuid: Mapped[str]
    discount: Mapped[Decimal]
    tracking_number: Mapped[str | None]
    payment_id: Mapped[int | None] = mapped_column(
        ForeignKey('payment.payment_id'),
    )
    order_status: Mapped[str]
    last_updated: Mapped[datetime]
    checked: Mapped[bool] = mapped_column(default=False)
    cancelled_at: Mapped[datetime | None]
    cancelled_reason: Mapped[str | None]


class OrderItems(Base):
    __tablename__ = 'order_items'

    order_items_id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey('order.order_id'))
    order = relationship(
        'Order',
        backref=backref('order_items', uselist=False),
        cascade='all,delete',
        foreign_keys=[order_id],
    )
    product_id: Mapped[int] = mapped_column(ForeignKey('product.product_id'))
    product = relationship(
        'Product',
        backref=backref('product', uselist=False),
        cascade='all,delete',
        foreign_keys=[product_id],
    )
    quantity: Mapped[int]
    price: Mapped[Decimal]
    discount_price: Mapped[Decimal]


class OrderStatusSteps(Base):
    __tablename__ = 'order_status_steps'

    order_status_steps_id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey('order.order_id'))
    status: Mapped[str]
    last_updated: Mapped[datetime]
    sending: Mapped[bool]
    active: Mapped[bool]
    description: Mapped[str | None]


class ImageGallery(Base):
    __tablename__ = 'image_gallery'

    category_id: Mapped[int] = mapped_column(primary_key=True)
    url: Mapped[str]
    product_id: Mapped[int] = mapped_column(ForeignKey('product.product_id'))


class Inventory(Base):
    __tablename__ = 'inventory'

    inventory_id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey('product.product_id'))
    product = relationship(
        'Product',
        backref=backref('inventory', uselist=False),
        cascade='all,delete',
        foreign_keys=[product_id],
    )
    order_id: Mapped[int | None] = mapped_column(ForeignKey('order.order_id'))
    order = relationship(
        'Order',
        backref=backref('inventory', uselist=False),
        cascade='all,delete',
        foreign_keys=[order_id],
    )
    quantity: Mapped[int]
    operation: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(default=datetime.now())
