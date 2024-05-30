from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic import Json
from sqlalchemy import JSON, ForeignKey, BIGINT
from sqlalchemy.orm import (
    DeclarativeBase,
    backref,
    Mapped,
    mapped_column,
    relationship,
)
from sqlalchemy.sql import func

from app.infra.constants import DocumentType


class Base(DeclarativeBase):
    pass


class RoleDB(Base):
    __tablename__ = 'role'

    role_id: Mapped[int] = mapped_column(primary_key=True)
    role: Mapped[str]
    active: Mapped[bool] = mapped_column(default=True)


class CategoryDB(Base):
    __tablename__ = 'category'

    category_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    path: Mapped[str]
    menu: Mapped[bool] = mapped_column(default=False)
    showcase: Mapped[bool] = mapped_column(default=False)
    image_path: Mapped[str | None]


class ProductDB(Base):
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
    category: Mapped['CategoryDB'] = relationship(
        foreign_keys=[category_id],
        backref='ProductDB',
        cascade='all,delete',
        uselist=False,
        lazy='joined',
    )
    inventory = relationship(
        'InventoryDB',
        backref=backref('ProductDB', uselist=False),
        cascade='all,delete',
        foreign_keys=[product_id],
        primaryjoin='ProductDB.product_id == InventoryDB.product_id',
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
    currency: Mapped[str] = mapped_column(default='BRL')


class CouponsDB(Base):
    __tablename__ = 'coupons'

    coupon_id: Mapped[int] = mapped_column(primary_key=True)
    affiliate_id: Mapped[int | None] = mapped_column(
        ForeignKey('user.user_id'),
    )
    user_id: Mapped[None | int] = mapped_column(ForeignKey('user.user_id'))
    product_id: Mapped[None | int] = mapped_column(
        ForeignKey('product.product_id'),
    )
    code: Mapped[str]
    discount: Mapped[Decimal]
    commission_percentage: Mapped[Decimal | None]
    qty: Mapped[int]
    active: Mapped[bool] = mapped_column(default=True)

    user = relationship(
        'UserDB',
        foreign_keys=[affiliate_id],
        lazy='joined',
        backref='Coupons',
        cascade='all,delete',
        uselist=False,
    )
    product = relationship(
        'ProductDB',
        foreign_keys=[product_id],
        backref='Coupons',
        cascade='all,delete',
        uselist=False,
    )


class OrderDB(Base):
    __tablename__ = 'order'

    order_id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('user.user_id'))
    user = relationship(
        'UserDB',
        foreign_keys=[user_id],
        backref='OrderDB',
        cascade='all,delete',
        uselist=False,
        lazy='joined',
    )
    affiliate_id: Mapped[int | None]
    customer_id: Mapped[str]
    order_date: Mapped[datetime]
    cart_uuid: Mapped[str]
    discount: Mapped[Decimal]
    tracking_number: Mapped[str | None]
    order_status: Mapped[str]
    last_updated: Mapped[datetime]
    checked: Mapped[bool] = mapped_column(default=False)
    cancelled_at: Mapped[datetime | None]
    cancelled_reason: Mapped[str | None]
    freight: Mapped[str | None]
    coupon_id: Mapped[int | None] = mapped_column(
        ForeignKey('coupons.coupon_id'),
    )


class OrderItemsDB(Base):
    __tablename__ = 'order_items'

    order_items_id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey('order.order_id'))
    order = relationship(
        'OrderDB',
        backref=backref('order_items', uselist=False),
        cascade='all,delete',
        foreign_keys=[order_id],
        lazy='joined',
    )
    product_id: Mapped[int] = mapped_column(ForeignKey('product.product_id'))
    product = relationship(
        'ProductDB',
        backref=backref('product', uselist=False),
        cascade='all,delete',
        foreign_keys=[product_id],
        lazy='joined',
    )
    quantity: Mapped[int]
    price: Mapped[Decimal]
    discount_price: Mapped[Decimal]


class OrderStatusStepsDB(Base):
    __tablename__ = 'order_status_steps'

    order_status_steps_id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey('order.order_id'))
    status: Mapped[str]
    last_updated: Mapped[datetime]
    sending: Mapped[bool]
    active: Mapped[bool]
    description: Mapped[str | None]


class ImageGalleryDB(Base):
    __tablename__ = 'image_gallery'

    category_id: Mapped[int] = mapped_column(primary_key=True)
    url: Mapped[str]
    product_id: Mapped[int] = mapped_column(ForeignKey('product.product_id'))


class InventoryDB(Base):
    __tablename__ = 'inventory'

    inventory_id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey('product.product_id'))
    order_id: Mapped[int | None] = mapped_column(ForeignKey('order.order_id'))
    order = relationship(
        'OrderDB',
        backref=backref('inventory', uselist=False),
        cascade='all,delete',
        foreign_keys=[order_id],
    )
    quantity: Mapped[int]
    operation: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(default=datetime.now())


class TransactionDB(Base):
    __tablename__ = 'transaction'

    transaction_id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('user.user_id'))
    user: Mapped['UserDB'] = relationship(
        foreign_keys=[user_id],
        backref='transaction',
        cascade='all,delete',
        uselist=False,
    )
    amount: Mapped[int]
    order_id: Mapped[int] = mapped_column(ForeignKey('order.order_id'))
    qty: Mapped[int]
    payment_id: Mapped[int] = mapped_column(ForeignKey('payment.payment_id'))
    status: Mapped[str]
    product_id: Mapped[int] = mapped_column(ForeignKey('product.product_id'))
    affiliate: Mapped[int | None] = mapped_column(ForeignKey('user.user_id'))
    affiliate_quota: Mapped[int | None]
    freight: Mapped[str | None]


class CustomerDB(Base):
    __tablename__ = 'customer'

    customer_id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('user.user_id'))
    user: Mapped['UserDB'] = relationship(
        foreign_keys=[user_id],
        backref='customer',
        cascade='all,delete',
        uselist=False,
    )
    customer_uuid: Mapped[str]
    payment_gateway: Mapped[str]
    payment_method: Mapped[str]
    token: Mapped[str]
    issuer_id: Mapped[str]
    status: Mapped[bool]
    created_at: Mapped[datetime] = mapped_column(default=func.now())


class PaymentDB(Base):
    __tablename__ = 'payment'

    payment_id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('user.user_id'))
    user: Mapped['UserDB'] = relationship(
        foreign_keys=[user_id],
        backref='payment',
        cascade='all,delete',
        uselist=False,
    )
    order_id: Mapped[int] = mapped_column(ForeignKey('order.order_id'))
    order: Mapped['OrderDB'] = relationship(
        foreign_keys=[order_id],
        backref='payment',
        cascade='all,delete',
        uselist=False,
    )
    amount: Mapped[Decimal]
    amount_with_fee: Mapped[Decimal] = mapped_column(server_default='0')
    token: Mapped[str]
    gateway_payment_id: Mapped[int] = mapped_column(BIGINT, server_default='0')
    status: Mapped[str]
    authorization: Mapped[str]
    payment_method: Mapped[str]
    payment_gateway: Mapped[str]
    installments: Mapped[int]
    processed: Mapped[bool] = mapped_column(default=False)
    processed_at: Mapped[datetime | None]
    freight_amount: Mapped[Decimal] = mapped_column(server_default='0')


class CreditCardFeeConfigDB(Base):
    __tablename__ = 'credit_card_fee_config'

    credit_card_fee_config_id: Mapped[int] = mapped_column(primary_key=True)
    min_installment_with_fee: Mapped[int]
    max_installments: Mapped[int]
    fee: Mapped[Decimal]
    active_date: Mapped[datetime] = mapped_column(default=func.now())


class UploadedImageDB(Base):
    __tablename__ = 'uploaded_image'

    uploaded_image_id: Mapped[int] = mapped_column(primary_key=True)
    original: Mapped[str]
    small: Mapped[str]
    thumb: Mapped[str]
    icon: Mapped[str]
    uploaded: Mapped[bool] = mapped_column(default=False)
    mimetype: Mapped[str] = mapped_column(nullable=True)
    name: Mapped[str] = mapped_column(nullable=True)
    size: Mapped[int] = mapped_column(nullable=True)
    image_bucket: Mapped[str] = mapped_column(nullable=True)


class UserDB(Base):
    __tablename__ = 'user'

    user_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    document: Mapped[str] = mapped_column(unique=True)
    username: Mapped[str] = mapped_column(unique=True)
    document_type: Mapped[str] = mapped_column(default=DocumentType.CPF.value)
    birth_date: Mapped[date] = mapped_column(nullable=True)
    gender: Mapped[str] = mapped_column(nullable=True)
    email: Mapped[str] = mapped_column(unique=True)
    phone: Mapped[str] = mapped_column(nullable=True)
    user_timezone: Mapped[str] = mapped_column(
        default='America/Sao_Paulo',
        nullable=True,
    )
    password: Mapped[str]
    role_id: Mapped[int] = mapped_column(default=2)
    active: Mapped[bool] = mapped_column(default=False)

    uuid: Mapped[str] = mapped_column(nullable=True)
    customer_id: Mapped[str] = mapped_column(nullable=True)
    card_id: Mapped[str] = mapped_column(nullable=True)
    payment_method: Mapped[str] = mapped_column(nullable=True)
    franchise_id: Mapped[str] = mapped_column(nullable=True)

    update_email_on_next_login: Mapped[bool] = mapped_column(
        default=False,
    )
    update_password_on_next_login: Mapped[bool] = mapped_column(
        default=False,
        server_default='0',
    )


class AddressDB(Base):
    __tablename__ = 'address'

    address_id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('user.user_id'))
    country: Mapped[str]
    city: Mapped[str]
    state: Mapped[str]
    neighborhood: Mapped[str]
    street: Mapped[str]
    street_number: Mapped[str]
    address_complement: Mapped[str]
    zipcode: Mapped[str]
    uuid: Mapped[str] = mapped_column(nullable=True)
    active: Mapped[bool] = mapped_column(default=False)


class UserResetPasswordDB(Base):
    __tablename__ = 'user_reset_password'

    user_reset_password_id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('user.user_id'))
    token: Mapped[str]
    used_token: Mapped[bool] = mapped_column(default=False)


class SalesCommissionDB(Base):
    __tablename__ = 'sales_commission'
    commissions_wallet_id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('user.user_id'))
    order_id: Mapped[int] = mapped_column(ForeignKey('order.order_id'))
    commission: Mapped[Decimal]
    date_created: Mapped[datetime]
    release_date: Mapped[datetime]
    released: Mapped[bool] = mapped_column(default=False)
    paid: Mapped[bool] = mapped_column(default=False)

    # Virtual relationship fields
    user: Mapped['UserDB'] = relationship(
        foreign_keys=[user_id],
        backref='sales_commission',
        uselist=False,
    )


class SettingsDB(Base):
    __tablename__ = 'settings'

    settings_id: Mapped[int] = mapped_column(primary_key=True)
    field: Mapped[str]
    value: Mapped[Json] = mapped_column(JSON)
    settings_category_id: Mapped[int]
    description: Mapped[str]
    is_active: Mapped[bool]
