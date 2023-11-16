import abc
from typing import Any, Self
from loguru import logger

from sqlalchemy import select
from sqlalchemy.orm import SessionTransaction
from app.entities.address import AddressBase
from app.entities.cart import ProductNotFoundError

from app.infra.models import order
from app.infra.models import users
from app.infra.models import transaction as transaction_model


class AddressNotFoundError(Exception):
    """Raised when a product is not found in the repository."""


class UserNotFoundError(Exception):
    """Raised when a product is not found in the repository."""


class AbstractRepository(abc.ABC):
    def __init__(self: Self) -> None:
        self.seen = set()  # type: Set[order.Product]

    async def get_product_by_id(self: Self, product_id: int) -> order.Product:
        return await self._get_product_by_id(product_id)

    async def get_product_by_sku(
        self: Self,
        sku: str,
    ) -> order.Product:
        product = await self._get_product_by_sku(sku)
        self.seen.add(product)
        return product

    def get_products(self: Self, products: list) -> order.Product:
        return self._get_products(products)

    def get_coupon_by_code(self: Self, code: str) -> order.Coupons:
        return self._get_coupon_by_code(code)

    def get_address_by_id(
        self: Self,
        address_id: int,
        user_address_id: int,
    ) -> users.Address:
        return self._get_address_by_id(address_id, user_address_id)

    def create_address(
        self: Self,
        address: AddressBase,
        user_id: int,
    ) -> users.Address:
        return self._create_address(address, user_id)

    def update_payment_method_to_user(
        self: Self,
        user_id: int,
        payment_method: str,
    ) -> users.User:
        return self._update_payment_method_to_user(
            user_id=user_id,
            payment_method=payment_method,
        )

    def get_user_by_email(
        self: Self,
        email: str,
    ) -> users.User:
        return self._get_user_by_email(email)

    @abc.abstractmethod
    async def _get_product_by_sku(
        self: Self,
        sku: str,
    ) -> order.Product:
        raise NotImplementedError

    @abc.abstractmethod
    async def _get_product_by_id(self: Self, product_id: int) -> order.Product:
        raise NotImplementedError

    @abc.abstractmethod
    def _get_products(self: Self, products: list) -> order.Product:
        raise NotImplementedError

    @abc.abstractmethod
    def _get_coupon_by_code(self: Self, code: str) -> order.Coupons:
        raise NotImplementedError

    @abc.abstractmethod
    def _get_address_by_id(
        self: Self,
        address_id: int,
        user_address_id: int,
    ) -> users.Address:
        raise NotImplementedError

    @abc.abstractmethod
    def _create_address(
        self: Self,
        address: users.Address,
        user_id: int,
    ) -> users.Address:
        raise NotImplementedError

    @abc.abstractmethod
    def _update_payment_method_to_user(
        self: Self,
        user_id: int,
        payment_method: str,
    ) -> users.User:
        raise NotImplementedError

    @abc.abstractmethod
    def _get_user_by_email(
        self: Self,
        email: str,
    ) -> users.User:
        raise NotImplementedError


class SqlAlchemyRepository(AbstractRepository):
    def __init__(self: Self, session: Any) -> None:   # noqa: ANN401
        super().__init__()
        self.session = session

    async def _get_product_by_sku(
        self: Self,
        sku: str,
    ) -> order.Product:
        """Query must return a valid product in search by sku."""
        async with self.session().begin() as session:
            product = await session.execute(
                select(order.Product).where(order.Product.sku == sku),
            )
            if not product:
                msg = f'No product with sku {sku}'
                raise ProductNotFoundError(msg)

            return product.fetchone()

    async def _get_product_by_id(self: Self, product_id: int) -> order.Product:
        """Must return a product by id."""
        async with self.session() as session:
            product = await session.execute(
                select(order.Product).where(
                    order.Product.product_id == product_id,
                ),
            )
            if not product:
                msg = f'No product with id {product_id}'
                raise ProductNotFoundError(msg)

            return product.scalars().first()

    async def _get_products(
        self: Self,
        products: list[int],
    ) -> list[order.Product]:
        """Must return updated products in db."""
        try:
            async with self.session() as session:
                products_db = await session.execute(
                    select(order.Product).where(
                        order.Product.product_id.in_(products),
                    ),
                )
                await _check_products_db(products_db, products)

                return products_db.scalars().all()
        except Exception as e:
            logger.error(f'Error in _get_products: {e}')
            raise

    async def _get_coupon_by_code(self: Self, code: str) -> order.Coupons:
        """Must return a coupon by code."""
        async with self.session() as session:
            coupon = await session.execute(
                select(order.Coupons).where(order.Coupons.code == code),
            )
            if not coupon:
                msg = f'No coupon with code {code}'
                raise ProductNotFoundError(msg)

            return coupon.scalar_one()

    async def _get_address_by_id(
        self: Self,
        address_id: int,
        user_address_id: int,
    ) -> users.Address:
        async with self.session() as session:
            address = await session.execute(
                select(users.Address).where(
                    users.Address.address_id == address_id,
                    users.Address.user_id == user_address_id,
                ),
            )
            if not address:
                msg = f'No address with id {address_id}'
                raise AddressNotFoundError(msg)

            return address.scalars().first()

    async def _create_address(
        self: Self,
        address: users.Address,
        user_id: int,
    ) -> users.Address:
        async with self.session() as session:
            address.user_id = user_id
            address_db = users.Address(**address.model_dump())
            session.add(address_db)
            await session.commit()

            return address_db

    async def _update_payment_method_to_user(
        self: Self,
        user_id: int,
        payment_method: str,
    ) -> users.User:
        async with self.session() as session:
            user = await session.execute(
                select(users.User).where(users.User.user_id == user_id),
            )
            if not user:
                msg = f'No user with id {user_id}'
                raise UserNotFoundError(msg)

            user = user.scalars().first()
            user.payment_method = payment_method
            await session.commit()
            return user

    async def _get_user_by_email(
        self: Self,
        email: str,
    ) -> users.User:
        """Must return user by email."""
        async with self.session() as session:
            user = await session.execute(
                select(users.User).where(users.User.email == email),
            )
            if not user:
                msg = f'No user with email {email}'
                raise UserNotFoundError(msg)

            return user.scalars().first()


async def get_coupon_by_code(
    code: str,
    *,
    transaction: SessionTransaction,
) -> order.Coupons:
    """Must return a coupon by code."""
    coupon = await transaction.session.scalar(
        select(order.Coupons).where(order.Coupons.code == code),
    )
    if not coupon:
        raise ProductNotFoundError

    return coupon


async def get_products(
    products: list[int],
    transaction: SessionTransaction,
) -> list[order.Product]:
    """Must return updated products in db."""
    try:
        products_db = await transaction.session.execute(
            select(order.Product).where(
                order.Product.product_id.in_(products),
            ),
        )
        await _check_products_db(products_db, products)

        return products_db.scalars().all()
    except Exception as e:
        logger.error(f'Error in _get_products: {e}')
        raise


async def _check_products_db(
    products_db: list,
    products: list[int],
) -> None:
    """Must check if all products are in db."""
    if not products_db:
        msg = f'No products with ids {products}'
        raise ProductNotFoundError(msg)


async def get_installment_fee(
    transaction: SessionTransaction,
    fee_config: int = 1,
) -> transaction_model.CreditCardFeeConfig:
    """Must return config fee."""
    try:
        config = await transaction.session.scalar(
            select(transaction_model.CreditCardFeeConfig).where(
                transaction_model.CreditCardFeeConfig.credit_card_fee_config_id == fee_config
                )
        )
        return config
    except Exception as e:
        logger.error(f'{e}')
        raise
