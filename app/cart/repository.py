import abc
from typing import Any, Self
from loguru import logger
from pydantic import TypeAdapter

from sqlalchemy import func, select
from sqlalchemy.orm import SessionTransaction, lazyload
from app.entities.address import AddressBase
from app.entities.cart import ProductNotFoundError
from sqlalchemy.exc import NoResultFound
from app.entities.coupon import CouponNotFoundError
from app.entities.product import ProductInDB

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
    def __init__(self: Self, session: Any) -> None:
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
            product = product.scalars().first()
            if not product:
                raise ProductNotFoundError
            return product

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
) -> models.CouponsDB:
    """Must return a coupon by code."""
    coupon = transaction.session.scalar(
        select(models.CouponsDB).where(models.CouponsDB.code == code),
    )
    if not coupon:
        raise ProductNotFoundError

    return coupon


async def get_products_quantity(
    products: list[int],
    transaction: SessionTransaction,
) -> list[ProductInDB]:
    """Must return products quantity."""
    try:
        quantity_query = (
            select(
                models.ProductDB.product_id,
                models.ProductDB.name,
                models.ProductDB.uri,
                models.ProductDB.price,
                models.ProductDB.active,
                models.ProductDB.direct_sales,
                models.ProductDB.description,
                models.ProductDB.image_path,
                models.ProductDB.installments_config,
                models.ProductDB.installments_list,
                models.ProductDB.discount,
                models.ProductDB.category_id,
                models.ProductDB.showcase,
                models.ProductDB.feature,
                models.ProductDB.show_discount,
                models.ProductDB.height,
                models.ProductDB.width,
                models.ProductDB.weight,
                models.ProductDB.length,
                models.ProductDB.diameter,
                models.ProductDB.sku,
                models.ProductDB.currency,
                func.coalesce(func.sum(models.InventoryDB.quantity), 0).label(
                    'quantity',
                ),
            )
            .options(lazyload('*'))
            .join(
                models.CategoryDB,
                models.CategoryDB.category_id == models.ProductDB.category_id,
            )
            .outerjoin(
                models.InventoryDB,
                models.ProductDB.product_id == models.InventoryDB.product_id,
            )
            .where(models.ProductDB.product_id.in_(products))
            .group_by(
                models.ProductDB.product_id,
                models.CategoryDB.category_id,
            )
        )
        products_db = await transaction.session.execute(quantity_query)
        adapter = TypeAdapter(list[ProductInDB])
        return adapter.validate_python(products_db.all())

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


async def _get_coupon_by_code(
    code: str,
    transaction: SessionTransaction,
) -> models.CouponsDB:
    """Must return a coupon by code."""
    try:
        async with transaction() as session:
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

async def get_product_by_id(
    product_id: int,
    transaction,
):
    """Must return a product by id."""
    product_query = select(
            models.ProductDB.product_id,
            models.ProductDB.name,
            models.ProductDB.uri,
            models.ProductDB.price,
            models.ProductDB.active,
            models.ProductDB.direct_sales,
            models.ProductDB.description,
            models.ProductDB.image_path,
            models.ProductDB.installments_config,
            models.ProductDB.installments_list,
            models.ProductDB.discount,
            models.ProductDB.category_id,
            models.ProductDB.showcase,
            models.ProductDB.feature,
            models.ProductDB.show_discount,
            models.ProductDB.height,
            models.ProductDB.width,
            models.ProductDB.weight,
            models.ProductDB.length,
            models.ProductDB.diameter,
            models.ProductDB.sku,
            models.ProductDB.currency,
            func.coalesce(func.sum(models.InventoryDB.quantity), 0).label(
                'quantity',
            ),
    ).options(lazyload('*')).outerjoin(
        models.InventoryDB,
        models.ProductDB.product_id == models.InventoryDB.product_id,
        ).where(
        models.ProductDB.product_id == product_id,
        ).group_by(
        models.ProductDB.product_id,
        )
    product = await transaction.session.execute(product_query)
    adapter = TypeAdapter(ProductInDB)
    product = adapter.validate_python(product.first())
    if not product:
        raise ProductNotFoundError
    return product

