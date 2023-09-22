# pylint: disable=attribute-defined-outside-init
from __future__ import annotations
import abc
from decimal import Decimal
from typing import Self
from app.entities.coupon import CouponBase, CouponResponse

from app.entities.product import ProductCart, ProductInDB
from app.cart import repository
from app.infra.custom_decorators import database_uow
from app.infra.database import get_async_session

from app.entities.user import UserAddress
from sqlalchemy.orm import SessionTransaction, sessionmaker
from app.entities.user import UserData
from app.entities.address import AddressBase
from app.payment import repository as payment_repository


class AbstractUnitOfWork(abc.ABC):
    cart = repository.AbstractRepository

    async def get_product_by_id(self: Self, product_id: int) -> ProductCart:
        """Must return a product by id."""
        return await self._get_product_by_id(product_id=product_id)

    async def get_products(self: Self, products: list) -> ProductCart:
        """Must return a product by id."""
        return await self._get_products(products=products)

    async def get_coupon_by_code(self: Self, code: str) -> CouponBase:
        """Must return a coupon by code."""
        return await self._get_coupon_by_code(code=code)

    async def get_address_by_id(
        self: Self,
        address_id: int,
        user_address_id: int,
    ) -> None:
        """Must return a address by id."""
        return await self._get_address_by_id(
            address_id=address_id,
            user_address_id=user_address_id,
        )

    async def create_address(
        self: Self,
        address: AddressBase,
        user: UserData,
    ) -> None:
        """Must create a address."""
        return await self._create_address(address=address, user=user)

    async def update_payment_method_to_user(
        self: Self,
        user_id: int,
        payment_method: str,
    ) -> None:
        """Must update payment method to user."""
        return await self._update_payment_method_to_user(
            user_id=user_id,
            payment_method=payment_method,
        )

    @abc.abstractmethod
    async def _get_product_by_id(self: Self, product_id: int) -> ProductCart:
        """Must return a product by id."""
        ...

    @abc.abstractmethod
    async def _get_products(self: Self, products: list) -> list:
        """Must return a product by id."""
        ...

    @abc.abstractmethod
    async def _get_coupon_by_code(self: Self, code: str) -> CouponBase:
        """Must return a coupon by code."""
        ...

    @abc.abstractmethod
    async def _get_address_by_id(
        self: Self,
        address_id: int,
        user_address_id: int,
    ) -> None:
        """Must return a address by id."""
        ...

    @abc.abstractmethod
    async def _create_address(
        self: Self,
        address: AddressBase,
        user: UserData,
    ) -> None:
        """Must create a address."""
        ...

    @abc.abstractmethod
    async def _update_payment_method_to_user(
        self: Self,
        user_id: int,
        payment_method: str,
    ) -> None:
        """Must update payment method to user."""
        ...


class SqlAlchemyUnitOfWork(AbstractUnitOfWork):
    def __init__(
        self: Self,
        session_factory: sessionmaker = get_async_session(),  # noqa: B008
    ) -> None:
        self.session = session_factory
        self.cart = repository.SqlAlchemyRepository(session_factory)

    async def _get_product_by_id(self: Self, product_id: int) -> ProductInDB:
        """Must return a product by id."""
        product_db = await self.cart.get_product_by_id(product_id=product_id)
        return ProductInDB.model_validate(product_db)

    async def _get_products(self: Self, products: list) -> list[ProductCart]:
        """Must return a products in list."""
        product_ids: list[int] = [item.product_id for item in products]
        products_db = await self.cart.get_products(products=product_ids)
        return [ProductInDB.model_validate(product) for product in products_db]

    async def _get_coupon_by_code(self: Self, code: str) -> CouponBase:
        """Must return a coupon by code."""
        coupon_db = await self.cart.get_coupon_by_code(code=code)
        return CouponBase.model_validate(coupon_db)

    async def _get_address_by_id(
        self: Self,
        address_id: int,
        user_address_id: int,
    ) -> UserAddress | None:
        """Must return a address by id."""
        address_db = await self.cart.get_address_by_id(
            address_id=address_id,
            user_address_id=user_address_id,
        )
        address_id = None
        if address_db:
            address_id = address_db.address_id
        return address_id

    async def _create_address(
        self: Self,
        address: AddressBase,
        user: UserData,
    ) -> None:
        """Must create a address."""
        user_db = await self.cart.get_user_by_email(email=user.email)
        address_db = await self.cart.create_address(
            address=address,
            user_id=user_db.user_id,
        )
        return address_db.address_id

    async def _update_payment_method_to_user(
        self: Self,
        user_id: int,
        payment_method: str,
    ) -> None:
        """Must update payment method to user."""
        await self.cart.update_payment_method_to_user(
            user_id=user_id,
            payment_method=payment_method,
        )


class MemoryUnitOfWork(AbstractUnitOfWork):
    async def _get_product_by_id(self: Self, product_id: int) -> ProductCart:
        """Must add product to new cart and return cart."""

        async def create_product_cart() -> ProductCart:
            return ProductCart(
                product_id=product_id,
                quantity=10,
                price=Decimal('10.00'),
            )

        return await create_product_cart()

    async def _get_products(
        self: Self,
        products: list[ProductInDB],
    ) -> list[ProductInDB]:
        """Must return a list of products."""
        _ = products

        async def return_product_list() -> list:
            return [
                ProductInDB(
                    product_id=1,
                    name='test_1',
                    uri='/test',
                    price=10000,
                    active=True,
                    direct_sales=False,
                    description='{ "test": "description" }',
                    discount=100,
                    category_id=1,
                    showcase=True,
                    show_discount=True,
                    upsell=None,
                    image_path='',
                    installments_config=1,
                    installments_list={},
                    height=None,
                    width=None,
                    weight=None,
                    length=None,
                    diameter=None,
                    sku='sku_1',
                ),
                ProductInDB(
                    product_id=2,
                    name='test_2',
                    uri='/test',
                    price=20000,
                    active=True,
                    direct_sales=False,
                    description='{ "test": "description 2" }',
                    discount=0,
                    category_id=1,
                    showcase=True,
                    show_discount=True,
                    upsell=None,
                    image_path='',
                    installments_config=1,
                    installments_list={},
                    height=None,
                    width=None,
                    weight=None,
                    length=None,
                    diameter=None,
                    sku='sku_2',
                ),
            ]

        return await return_product_list()

    async def _get_coupon_by_code(self: Self, code: str) -> CouponBase:
        return CouponBase(
            code=code,
            coupon_fee=Decimal('10.00'),
        )

    async def _get_address_by_id(self: Self, address_id: int) -> None:
        ...

    async def _create_address(
        self: Self,
        address: AddressBase,
        user_id: int,
    ) -> None:
        ...

    async def _update_payment_method_to_user(
        self: Self,
        user_id: int,
        payment_method: str,
    ) -> None:
        ...


async def get_coupon_by_code(
    code: str,
    *,
    transaction: SessionTransaction,
) -> CouponResponse:
    """Must return a coupon by code."""
    coupon_db = await repository.get_coupon_by_code(
        code, transaction=transaction
    )
    return CouponResponse.model_validate(coupon_db)


@database_uow()
async def get_customer(
    user_id: int,
    *,
    payment_gateway: str,
    bootstrap: Any,
    transaction: SessionTransaction | None,
) -> str | None:
    """Must return a customer by user id."""
    if not transaction:
        msg = 'Transaction must be provided'
        raise ValueError(msg)
    customer = await payment_repository.get_customer(
        user_id,
        payment_gateway=payment_gateway,
        transaction=transaction
    )
    custumer_uuid = None
    if customer:
        custumer_uuid = customer.customer_uuid
    return custumer_uuid
