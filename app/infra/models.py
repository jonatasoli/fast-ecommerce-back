from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any

from pydantic import Json
from sqlalchemy import JSON, ForeignKey, BIGINT, Text, DateTime, select, func
from sqlalchemy.orm import (
    DeclarativeBase,
    backref,
    Mapped,
    mapped_column,
    relationship,
    column_property,
)
from sqlalchemy.ext.hybrid import hybrid_property

from app.infra.constants import DiscountType, DocumentType


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


class InventoryDB(Base):
    __tablename__ = 'inventory'

    inventory_id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey('product.product_id'))
    product: Mapped['ProductDB'] = relationship(
        'ProductDB',
        back_populates='inventory',
    )
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
        backref='products',
        cascade='all,delete',
        uselist=False,
        lazy='joined',
    )
    inventory = relationship('InventoryDB', back_populates='product')
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

    quantity = column_property(
        select(func.coalesce(func.sum(InventoryDB.quantity), 0))
        .where(InventoryDB.product_id == product_id)
        .correlate_except(InventoryDB)
        .scalar_subquery(),
    )


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
    discount_price: Mapped[Decimal | None]
    limit_price: Mapped[Decimal | None]
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
    amount: Mapped[Decimal]
    amount_with_fee: Mapped[Decimal] = mapped_column(server_default='0')
    token: Mapped[str]
    gateway_payment_id: Mapped[str]
    status: Mapped[str]
    authorization: Mapped[str]
    payment_method: Mapped[str]
    payment_gateway: Mapped[str]
    installments: Mapped[int]
    processed: Mapped[bool] = mapped_column(default=False)
    processed_at: Mapped[datetime | None]
    freight_amount: Mapped[Decimal] = mapped_column(server_default='0')

    order: Mapped['OrderDB'] = relationship(
        'OrderDB',
        back_populates='payment',
        foreign_keys=[order_id],
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

    items: Mapped[list['OrderItemsDB']] = relationship(
        'OrderItemsDB',
        backref='orders',
        cascade='all,delete',
        foreign_keys='OrderItemsDB.order_id',
        lazy='joined',
        overlaps='order_items',
    )
    payment: Mapped['PaymentDB'] = relationship(
        'PaymentDB',
        foreign_keys=[PaymentDB.order_id],
        back_populates='order',
        uselist=False,
        lazy='joined',
    )


class OrderItemsDB(Base):
    __tablename__ = 'order_items'

    order_items_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(ForeignKey('order.order_id'))
    order = relationship(
        'OrderDB',
        backref=backref('order_items', overlaps='items,orders'),
        cascade='all,delete',
        foreign_keys=[order_id],
        lazy='joined',
        overlaps='orders, items',
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


class MediaGalleryDB(Base):
    __tablename__ = 'image_gallery'

    media_gallery_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    media_id: Mapped[int] = mapped_column(ForeignKey('uploaded_media.media_id'))
    product_id: Mapped[int] = mapped_column(ForeignKey('product.product_id'))


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


class CreditCardFeeConfigDB(Base):
    __tablename__ = 'credit_card_fee_config'

    credit_card_fee_config_id: Mapped[int] = mapped_column(primary_key=True)
    min_installment_with_fee: Mapped[int]
    max_installments: Mapped[int]
    fee: Mapped[Decimal]
    active_date: Mapped[datetime] = mapped_column(default=func.now())


class UploadedMediaDB(Base):
    __tablename__ = 'uploaded_media'

    media_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    type: Mapped[str]
    uri: Mapped[str]
    small: Mapped[str] = mapped_column(nullable=True)
    thumb: Mapped[str] = mapped_column(nullable=True)
    alt: Mapped[str] = mapped_column(nullable=True)
    caption: Mapped[str] = mapped_column(nullable=True)
    order: Mapped[int]
    active: Mapped[bool] = mapped_column(default=True)
    image_bucket: Mapped[str] = mapped_column(nullable=True)
    create_at: Mapped[datetime] = mapped_column(default=func.now())
    update_at: Mapped[datetime] = mapped_column(default=func.now())


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

    update_email_on_next_login: Mapped[bool] = mapped_column(
        default=False,
    )
    update_password_on_next_login: Mapped[bool] = mapped_column(
        default=False,
        server_default='0',
    )
    terms: Mapped[bool] = mapped_column(
        default=False,
        server_default='0',
    )

    addresses: Mapped[list['AddressDB'] | None] = relationship(
        'AddressDB',
        back_populates='user',
        cascade='all, delete',
        lazy='joined',
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

    user: Mapped['UserDB'] = relationship(
        'UserDB',
        back_populates='addresses',
    )


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
    payment_id: Mapped[int] = mapped_column(ForeignKey('payment.payment_id'))
    released: Mapped[bool] = mapped_column(default=False)
    paid: Mapped[bool] = mapped_column(default=False)
    active: Mapped[bool] = mapped_column(default=False)
    cancelled: Mapped[bool] = mapped_column(default=False, server_default='0')
    cancelled_at: Mapped[datetime | None]

    user: Mapped['UserDB'] = relationship(
        foreign_keys=[user_id],
        backref='sales_commission',
        uselist=False,
        lazy='joined',
    )


class SettingsDB(Base):
    __tablename__ = 'settings'

    settings_id: Mapped[int] = mapped_column(primary_key=True)
    locale: Mapped[str]
    provider: Mapped[str]
    field: Mapped[str]
    value: Mapped[Json] = mapped_column(JSON)
    credentials: Mapped[str | None]
    description: Mapped[str | None]
    is_active: Mapped[bool] = mapped_column(default=True)
    is_default: Mapped[bool] = mapped_column(default=False)


class InformUserProductDB(Base):
    __tablename__ = 'inform_product_user'

    inform_product_user_id: Mapped[int] = mapped_column(primary_key=True)
    user_mail: Mapped[str]
    user_phone: Mapped[str]
    product_id: Mapped[int]
    product_name: Mapped[str]
    sended: Mapped[bool]


class FeeDB(Base):
    __tablename__ = 'fees'

    fee_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    fee_type: Mapped[str]
    value: Mapped[Decimal]
    active: Mapped[bool] = mapped_column(default=True)


class CoProducerFeeDB(Base):
    __tablename__ = 'co_producer_fees'

    co_producer_fee_id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('user.user_id'))
    percentage: Mapped[Decimal]
    active: Mapped[bool] = mapped_column(default=True)


class CampaignDB(Base):
    __tablename__ = 'campaign'

    campaign_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    start_date: Mapped[datetime]
    end_date: Mapped[datetime]
    active: Mapped[bool] = mapped_column(default=True)
    discount_type: Mapped[str]
    discount_value: Mapped[Decimal | None]
    free_shipping: Mapped[bool]
    min_purchase_value: Mapped[Decimal | None]
    commission_fee_value: Mapped[Decimal | None]


class CategoryMediaGalleryDB(Base):
    __tablename__ = 'category_media_gallery'

    category_media_gallery_id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )
    media_id: Mapped[int] = mapped_column(ForeignKey('uploaded_media.media_id'))
    category_id: Mapped[int] = mapped_column(ForeignKey('category.category_id'))


class ProjectDB(Base):
    __tablename__ = 'crowdfunding_project'

    project_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('user.user_id'))
    creator: Mapped['UserDB'] = relationship(
        foreign_keys=[user_id],
        backref='crowdfunding_projects',
        uselist=False,
        lazy='joined',
    )
    title: Mapped[str]
    slug: Mapped[str] = mapped_column(unique=True)
    description: Mapped[Json] = mapped_column(JSON, nullable=True) 
    short_description: Mapped[str | None]
    story: Mapped[Json] = mapped_column(JSON, nullable=True)
    risks_and_challenges: Mapped[Json] = mapped_column(JSON, nullable=True)
    main_image: Mapped[str | None]
    video_url: Mapped[str | None]
    category: Mapped[str | None]
    location: Mapped[str | None]
    start_date: Mapped[datetime]
    end_date: Mapped[datetime]
    goal_amount: Mapped[Decimal]
    current_amount: Mapped[Decimal] = mapped_column(default=Decimal('0'))
    backers_count: Mapped[int] = mapped_column(default=0)
    active: Mapped[bool] = mapped_column(default=True)
    published: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime] = mapped_column(default=func.now(), onupdate=func.now())

    tiers: Mapped[list['TierDB']] = relationship(
        'TierDB',
        back_populates='project',
        cascade='all,delete',
        lazy='joined',
    )
    contributions: Mapped[list['ContributionDB']] = relationship(
        'ContributionDB',
        back_populates='project',
        cascade='all,delete',
        lazy='joined',
    )
    goals: Mapped[list['GoalDB']] = relationship(
        'GoalDB',
        back_populates='project',
        cascade='all,delete',
        lazy='joined',
    )
    monthly_goals: Mapped[list['MonthlyGoalDB']] = relationship(
        'MonthlyGoalDB',
        back_populates='project',
        cascade='all,delete',
        lazy='joined',
    )


class TierDB(Base):
    __tablename__ = 'crowdfunding_tier'

    tier_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey('crowdfunding_project.project_id'))
    project: Mapped['ProjectDB'] = relationship(
        'ProjectDB',
        back_populates='tiers',
        foreign_keys=[project_id],
        uselist=False,
        lazy='joined',
    )
    name: Mapped[str]
    description: Mapped[str | None]
    amount: Mapped[Decimal]
    is_recurring: Mapped[bool] = mapped_column(default=False)
    recurring_interval: Mapped[str | None]
    max_backers: Mapped[int | None]
    current_backers: Mapped[int] = mapped_column(default=0)
    estimated_delivery: Mapped[date | None]
    active: Mapped[bool] = mapped_column(default=True)
    order: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime] = mapped_column(default=func.now(), onupdate=func.now())

    contributions: Mapped[list['ContributionDB']] = relationship(
        'ContributionDB',
        back_populates='tier',
        cascade='all,delete',
        lazy='joined',
    )


class ContributionDB(Base):
    __tablename__ = 'crowdfunding_contribution'

    contribution_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey('crowdfunding_project.project_id'))
    project: Mapped['ProjectDB'] = relationship(
        'ProjectDB',
        back_populates='contributions',
        foreign_keys=[project_id],
        uselist=False,
        lazy='joined',
    )
    tier_id: Mapped[int | None] = mapped_column(ForeignKey('crowdfunding_tier.tier_id'))
    tier: Mapped['TierDB'] = relationship(
        'TierDB',
        back_populates='contributions',
        foreign_keys=[tier_id],
        uselist=False,
        lazy='joined',
    )
    user_id: Mapped[int] = mapped_column(ForeignKey('user.user_id'))
    user: Mapped['UserDB'] = relationship(
        foreign_keys=[user_id],
        backref='crowdfunding_contributions',
        uselist=False,
        lazy='joined',
    )
    amount: Mapped[Decimal]
    is_recurring: Mapped[bool] = mapped_column(default=False)
    recurring_subscription_id: Mapped[str | None]
    payment_id: Mapped[int | None] = mapped_column(ForeignKey('payment.payment_id'))
    payment: Mapped['PaymentDB'] = relationship(
        'PaymentDB',
        foreign_keys=[payment_id],
        uselist=False,
        lazy='joined',
    )
    status: Mapped[str] = mapped_column(default='pending')
    anonymous: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime] = mapped_column(default=func.now(), onupdate=func.now())


class GoalDB(Base):
    __tablename__ = 'crowdfunding_goal'

    goal_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey('crowdfunding_project.project_id'))
    project: Mapped['ProjectDB'] = relationship(
        'ProjectDB',
        back_populates='goals',
        foreign_keys=[project_id],
        uselist=False,
        lazy='joined',
    )
    title: Mapped[str]
    description: Mapped[str | None]
    target_amount: Mapped[Decimal]
    current_amount: Mapped[Decimal] = mapped_column(default=Decimal('0'))
    achieved: Mapped[bool] = mapped_column(default=False)
    achieved_at: Mapped[datetime | None]
    order: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime] = mapped_column(default=func.now(), onupdate=func.now())


class MonthlyGoalDB(Base):
    __tablename__ = 'crowdfunding_monthly_goal'

    monthly_goal_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey('crowdfunding_project.project_id'))
    project: Mapped['ProjectDB'] = relationship(
        'ProjectDB',
        back_populates='monthly_goals',
        foreign_keys=[project_id],
        uselist=False,
        lazy='joined',
    )
    month: Mapped[int]
    year: Mapped[int]
    target_amount: Mapped[Decimal]
    current_amount: Mapped[Decimal] = mapped_column(default=Decimal('0'))
    achieved: Mapped[bool] = mapped_column(default=False)
    achieved_at: Mapped[datetime | None]
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime] = mapped_column(default=func.now(), onupdate=func.now())


class CheckoutJobDB(Base):
    __tablename__ = 'checkout_jobs'

    checkout_job_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    cart_uuid: Mapped[str] = mapped_column(unique=True, index=True)
    payment_gateway: Mapped[str]
    payment_method: Mapped[str]
    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(default='pending')
    attempts: Mapped[int] = mapped_column(default=0)
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    order_id: Mapped[str | None] = mapped_column(nullable=True)
    gateway_payment_id: Mapped[str | None] = mapped_column(nullable=True)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
