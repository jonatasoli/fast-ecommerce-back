from datetime import datetime
from decimal import Decimal
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infra.models.base import Base


class SalesComission(Base):
    __tablename__ = 'sales_commission'

    commissions_wallet_id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('user.user_id'))
    user: Mapped['User'] = relationship(  # noqa: F821
        foreign_keys=[user_id],
        backref='transaction',
        cascade='all,delete',
        uselist=False,
        lazy='joined',
    )
    order_id: Mapped[int] = mapped_column(ForeignKey('order.order_id'))
    order: Mapped['Order'] = relationship(  # noqa: F821
        foreign_keys=[order_id],
        backref='transaction',
        cascade='all,delete',
        uselist=False,
        lazy='joined',
    )
    commission: Mapped[Decimal]
    date_created: Mapped[datetime]
    released: Mapped[bool]
    paid: Mapped[bool]
