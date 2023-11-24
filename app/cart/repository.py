import abc
from typing import Any, Self
from loguru import logger

from sqlalchemy import func, select
from sqlalchemy.orm import Session, SessionTransaction
from app.entities.address import AddressBase
from app.entities.cart import ProductNotFoundError
from sqlalchemy.exc import NoResultFound
from app.entities.coupon import CouponNotFoundError

from app.infra import models


class AddressNotFoundError(Exception):
    """Raised when a product is not found in the repository."""


class UserNotFoundError(Exception):
    """Raised when a product is not found in the repository."""


class AbstractRepository(abc.ABC):
    def __init__(self: Self) -> None:
        self.seen = set()  # type: Set[order.Product]

    async def get_product_by_id(
        self: Self,
        product_id: int,
    ) -> models.ProductDB:
        return await self._get_product_by_id(product_id)

    async def get_product_by_sku(
        self: Self,
        sku: str,
    ) -> models.ProductDB:
        product = await self._get_product_by_sku(sku)
        self.seen.add(product)
        return product

    def get_products(self: Self, products: list) -> models.ProductDB:
        return self._get_products(products)

    def get_coupon_by_code(self: Self, code: str) -> models.CouponsDB:
        return self._get_coupon_by_code(code)

    def get_address_by_id(
        self: Self,
        address_id: int,
        user_address_id: int,
    ) -> models.AddressDB:
        return self._get_address_by_id(address_id, user_address_id)

    def create_address(
        self: Self,
        address: AddressBase,
        user_id: int,
    ) -> models.AddressDB:
        return self._create_address(address, user_id)

    def update_payment_method_to_user(
        self: Self,
        user_id: int,
        payment_method: str,
    ) -> models.UserDB:
        return self._update_payment_method_to_user(
            user_id=user_id,
            payment_method=payment_method,
        )

    def get_user_by_email(
        self: Self,
        email: str,
    ) -> models.UserDB:
        return self._get_user_by_email(email)

    @abc.abstractmethod
    async def _get_product_by_sku(
        self: Self,
        sku: str,
    ) -> models.ProductDB:
        raise NotImplementedError

    @abc.abstractmethod
    async def _get_product_by_id(
        self: Self,
        product_id: int,
    ) -> models.ProductDB:
        raise NotImplementedError

    @abc.abstractmethod
    def _get_products(self: Self, products: list) -> models.ProductDB:
        raise NotImplementedError

    @abc.abstractmethod
    def _get_coupon_by_code(self: Self, code: str) -> models.CouponsDB:
        raise NotImplementedError

    @abc.abstractmethod
    def _get_address_by_id(
        self: Self,
        address_id: int,
        user_address_id: int,
    ) -> models.AddressDB:
        raise NotImplementedError

    @abc.abstractmethod
    def _create_address(
        self: Self,
        address: models.AddressDB,
        user_id: int,
    ) -> models.AddressDB:
        raise NotImplementedError

    @abc.abstractmethod
    def _update_payment_method_to_user(
        self: Self,
        user_id: int,
        payment_method: str,
    ) -> models.UserDB:
        raise NotImplementedError

    @abc.abstractmethod
    def _get_user_by_email(
        self: Self,
        email: str,
    ) -> models.UserDB:
        raise NotImplementedError


class SqlAlchemyRepository(AbstractRepository):
    def __init__(self: Self, session: Any) -> None:   # noqa: ANN401
        super().__init__()
        self.session = session

    async def _get_product_by_sku(
        self: Self,
        sku: str,
    ) -> models.ProductDB:
        """Query must return a valid product in search by sku."""
        async with self.session().begin() as session:
            product = await session.execute(
                select(models.ProductDB).where(models.ProductDB.sku == sku),
            )
            if not product:
                msg = f'No product with sku {sku}'
                raise ProductNotFoundError(msg)

            return product.fetchone()

    async def _get_product_by_id(
        self: Self,
        product_id: int,
    ) -> models.ProductDB:
        """Must return a product by id."""
        async with self.session() as session:
            product = await session.execute(
                select(models.ProductDB).where(
                    models.ProductDB.product_id == product_id,
                ),
            )
            if not product:
                msg = f'No product with id {product_id}'
                raise ProductNotFoundError(msg)

            return product.scalars().first()

    async def _get_products(
        self: Self,
        products: list[int],
    ) -> list[models.ProductDB]:
        """Must return updated products in db."""
        try:
            async with self.session() as session:
                products_db = await session.execute(
                    select(models.ProductDB).where(
                        models.ProductDB.product_id.in_(products),
                    ),
                )
                await _check_products_db(products_db, products)

                return products_db.scalars().all()
        except Exception as e:
            logger.error(f'Error in _get_products: {e}')
            raise

    async def _get_coupon_by_code(self: Self, code: str) -> models.CouponsDB:
        """Must return a coupon by code."""
        try:
            async with self.session() as session:
                coupon = await session.execute(
                    select(models.CouponsDB).where(
                        models.CouponsDB.code == code,
                    ),
                )
                if not coupon:
                    msg = f'No coupon with code {code}'
                    raise ProductNotFoundError(msg)

                return coupon.scalar_one()
        except NoResultFound as nrf:
            raise CouponNotFoundError from nrf

    async def _get_address_by_id(
        self: Self,
        address_id: int,
        user_address_id: int,
    ) -> models.AddressDB:
        async with self.session() as session:
            address = await session.execute(
                select(models.AddressDB).where(
                    models.AddressDB.address_id == address_id,
                    models.AddressDB.user_id == user_address_id,
                ),
            )
            if not address:
                msg = f'No address with id {address_id}'
                raise AddressNotFoundError(msg)

            return address.scalars().first()

    async def _create_address(
        self: Self,
        address: models.AddressDB,
        user_id: int,
    ) -> models.AddressDB:
        async with self.session() as session:
            address.user_id = user_id
            address_db = models.AddressDB(**address.model_dump())
            session.add(address_db)
            await session.commit()

            return address_db

    async def _update_payment_method_to_user(
        self: Self,
        user_id: int,
        payment_method: str,
    ) -> models.UserDB:
        async with self.session() as session:
            user = await session.execute(
                select(models.UserDB).where(models.UserDB.user_id == user_id),
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
    ) -> models.UserDB:
        """Must return user by email."""
        async with self.session() as session:
            user = await session.execute(
                select(models.UserDB).where(models.UserDB.email == email),
            )
            if not user:
                msg = f'No user with email {email}'
                raise UserNotFoundError(msg)

            return user.scalars().first()


async def get_coupon_by_code(
    code: str,
    *,
    transaction: SessionTransaction,
) -> models.CouponsDB:
    """Must return a coupon by code."""
    coupon = await transaction.session.scalar(
        select(models.CouponsDB).where(models.CouponsDB.code == code),
    )
    if not coupon:
        raise ProductNotFoundError

    return coupon


def sync_get_coupon_by_code(
    code: str,
    *,
    transaction: SessionTransaction,
) -> models.CouponsDB:
    """Must return a coupon by code."""
    coupon = transaction.session.scalar(
        select(models.CouponsDB).where(models.CouponsDB.code == code),
    )
    if not coupon:
        raise ProductNotFoundError

    return coupon


def sync_get_coupon_by_code(
    code: str,
    *,
    transaction: SessionTransaction,
) -> order.Coupons:
    """Must return a coupon by code."""
    coupon = transaction.session.scalar(
        select(order.Coupons).where(order.Coupons.code == code),
    )
    if not coupon:
        raise ProductNotFoundError

    return coupon

async def get_products(
    products: list[int],
    transaction: SessionTransaction,
) -> list[models.ProductDB]:
    """Must return updated products in db."""
    try:
        products_db = await transaction.session.execute(
            select(models.ProductDB).where(
                models.ProductDB.product_id.in_(products),
            ),
        )
        await _check_products_db(products_db, products)

        return products_db.scalars().all()
    except Exception as e:
        logger.error(f'Error in _get_products: {e}')
        raise


def sync_get_products(
    products: list[int],
    transaction: Session,
) -> list[order.Product]:
    """Must return updated products in db."""
    try:
        products_db = transaction.execute(
            select(order.Product).where(
                order.Product.product_id.in_(products),
            ),
        )
        _check_products_db(products_db, products)

        return products_db.scalars().all()
    except Exception as e:
        logger.error(f'Error in _get_products: {e}')
        raise

async def get_products_quantity(
    products: list[int],
    transaction: SessionTransaction,
) -> list[models.ProductDB]:
    """Must return products quantity."""
    try:
        quantity_query = (
            select(
                models.InventoryDB.product_id.label('product_id'),
                func.coalesce(func.sum(models.InventoryDB.quantity), 0).label(
                    'quantity',
                ),
            )
            .outerjoin(
                models.ProductDB,
                models.ProductDB.product_id == models.InventoryDB.product_id,
            )
            .where(models.ProductDB.product_id.in_(products))
            .group_by(models.InventoryDB.product_id)
        )
        products_db = await transaction.session.execute(quantity_query)
        await _check_products_db(products_db, products)

        column_names = products_db.keys()
        products = products_db.all()

        products_list = []
        for product in products:
            product_dict = dict(zip(column_names, product))
            products_list.append(product_dict)

        return products_list
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
) -> models.CreditCardFeeConfigDB:
    """Must return config fee."""
    try:
        config = await transaction.session.scalar(
            select(models.CreditCardFeeConfigDB).where(
                models.CreditCardFeeConfigDB.credit_card_fee_config_id
                == fee_config,
            ),
        )
        return config
    except Exception as e:
        logger.error(f'{e}')
        raise
