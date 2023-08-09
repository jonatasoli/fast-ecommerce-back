from datetime import date
from sqlalchemy import ForeignKey

from constants import DocumentType
from app.infra.models.base import Base
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column


class User(Base):
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
    franchise_id: Mapped[str] = mapped_column(nullable=True)

    update_email_on_next_login: Mapped[bool] = mapped_column(
        default=False,
    )
    update_password_on_next_login: Mapped[bool] = mapped_column(
        default=False,
        server_default='0',
    )


class Address(Base):
    __tablename__ = 'address'

    address_id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('user.user_id'))
    type_address: Mapped[str]
    category: Mapped[str]
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


class UserResetPassword(Base):
    __tablename__ = 'user_reset_password'

    user_reset_password_id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('user.user_id'))
    token: Mapped[str]
    used_token: Mapped[bool] = mapped_column(default=False)
