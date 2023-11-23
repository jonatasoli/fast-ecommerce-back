from datetime import datetime
from decimal import Decimal
from sqlalchemy import (
    ForeignKey,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.infra.models.base import Base
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column


class Transaction(Base):
    __tablename__ = 'transaction'

    transaction_id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('user.user_id'))
    user: Mapped['User'] = relationship(  # noqa: F821
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


class Customer(Base):
    __tablename__ = 'customer'

    customer_id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('user.user_id'))
    user: Mapped['User'] = relationship(  # noqa: F821
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


class Payment(Base):
    __tablename__ = 'payment'

    payment_id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('user.user_id'))
    user: Mapped['User'] = relationship(  # noqa: F821
        foreign_keys=[user_id],
        backref='payment',
        cascade='all,delete',
        uselist=False,
    )
    order_id: Mapped[int] = mapped_column(ForeignKey('order.order_id'))
    order: Mapped['Order'] = relationship(  # noqa: F821
        foreign_keys=[order_id],
        backref='payment',
        cascade='all,delete',
        uselist=False,
    )
    amount: Mapped[Decimal]
    amount_with_fee: Mapped[Decimal] = mapped_column(server_default='0')
    token: Mapped[str]
    gateway_payment_id: Mapped[int] = mapped_column(server_default='0')
    status: Mapped[str]
    authorization: Mapped[str]
    payment_method: Mapped[str]
    payment_gateway: Mapped[str]
    installments: Mapped[int]
    processed: Mapped[bool] = mapped_column(default=False)
    processed_at: Mapped[datetime | None]
    freight_amount: Mapped[Decimal] = mapped_column(server_default='0')


class CreditCardFeeConfig(Base):
    __tablename__ = 'credit_card_fee_config'

    credit_card_fee_config_id: Mapped[int] = mapped_column(primary_key=True)
    min_installment_with_fee: Mapped[int]
    max_installments: Mapped[int]
    fee: Mapped[Decimal]
    active_date: Mapped[datetime] = mapped_column(default=func.now())
