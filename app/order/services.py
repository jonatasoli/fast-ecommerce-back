from datetime import UTC, datetime
import math

from app.entities.user import UserAddressInDB
from app.infra.constants import CurrencyType, OrderStatus, PaymentStatus
from fastapi import HTTPException, status
from app.infra.database import get_async_session
from loguru import logger
from pydantic import TypeAdapter
from sqlalchemy import asc, func, select
from sqlalchemy.orm import Session, joinedload, lazyload, selectinload
from app.product import repository
from app.payment import repository as repository_payment
from app.order import repository as  repository_order
from faststream.rabbit import RabbitQueue

from app.entities.order import CancelOrder, OrderInDB, OrderNotFoundError, OrderResponse
from app.entities.product import (
    ProductCategoryInDB,
    ProductInDB,
    ProductNotFoundError,
    ProductPatchRequest,
    ProductsResponse,
)
from app.infra.models import (
    AddressDB,
    CategoryDB,
    InventoryDB,
    ProductDB,
    OrderDB,
    OrderItemsDB,
    UserDB,
)
from app.entities.order import (
    CategoryInDB,
    OrderFullResponse,
    OrderSchema,
    TrackingFullResponse,
    OrderUserListResponse,
    ProductListOrderResponse,
)


class NotFoundCategoryError(Exception):
    """Not Found Category Exception."""


def get_product(db: Session, uri: str) -> ProductInDB | None:
    """Return specific product."""
    with db:
        query_product = (
            select(
                ProductDB.product_id,
                ProductDB.name,
                ProductDB.uri,
                ProductDB.price,
                ProductDB.active,
                ProductDB.direct_sales,
                ProductDB.description,
                ProductDB.image_path,
                ProductDB.installments_config,
                ProductDB.installments_list,
                ProductDB.discount,
                ProductDB.category_id,
                ProductDB.showcase,
                ProductDB.feature,
                ProductDB.show_discount,
                ProductDB.height,
                ProductDB.width,
                ProductDB.weight,
                ProductDB.length,
                ProductDB.diameter,
                ProductDB.sku,
                ProductDB.currency,
                func.coalesce(func.sum(InventoryDB.quantity), 0).label(
                    'quantity',
                ),
            )
            .options(lazyload('*'))
            .where(ProductDB.uri == uri)
            .where(ProductDB.active.is_(True))
            .join(
                CategoryDB,
                CategoryDB.category_id == ProductDB.category_id,
            )
            .outerjoin(
                InventoryDB,
                ProductDB.product_id == InventoryDB.product_id,
            )
            .group_by(
                ProductDB.product_id,
                CategoryDB.category_id,
            )
            .order_by(ProductDB.product_id.desc())
        )

        productdb = db.execute(query_product)
    if not productdb:
        raise ProductNotFoundError
    return ProductInDB.model_validate(productdb.first())


def update_product(product: ProductDB, product_data: dict) -> ProductDB:
    """Update product by id."""
    for key, value in product_data.items():
        setattr(product, key, value)
    return product


async def patch_product(
    product_id,
    *,
    product_data: ProductPatchRequest,
    db,
) -> None:
    """Update Product."""
    values = product_data.model_dump(exclude_none=True)
    product = await get_product_by_id(db, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Product not found',
        )
    async with db:
        update_product(product, values)
        db.commit()


async def complete_order(
    order_id,
    *,
    db,
) -> None:
    """Complete Order."""
    async with db().begin() as transaction:
        order_query = select(OrderDB).where(OrderDB.order_id==order_id)
        order = await transaction.session.scalar(order_query)

        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Order not found',
            )
        order.order_status = OrderStatus.SHIPPING_COMPLETE.value
        transaction.session.add(order)
        transaction.session.commit()


def delete_product(db: Session, product_id: int) -> None:
    """Remove Product."""
    with db:
        db.execute(
            select(ProductDB).where(ProductDB.product_id == product_id),
        ).delete()
        db.commit()


def get_showcase(*, currency, db) -> list:
    """Get Products showcase."""
    with db() as transaction:
        showcases_query = (
            select(ProductDB)
            .where(ProductDB.showcase.is_(True))
            .where(ProductDB.currency.like(currency))
            .where(ProductDB.active.is_(True))
        )
        showcases = transaction.execute(showcases_query).scalars().all()
        adapter = TypeAdapter(list[ProductCategoryInDB])

    return adapter.validate_python(showcases)

async def get_product_by_id(product_id: int, db) -> ProductInDB:
    """Search product by id."""
    async with db().begin() as transaction:
        product_db = await repository.get_product_by_id(
            product_id,
            transaction=transaction,
        )
    return ProductInDB.model_validate(product_db)



def get_orders(page, offset, *, db):
    """Get Orders Paid."""
    with db().begin() as db: # Noqa: PLR1704
        orders_query = (
            select(OrderDB).options(
                joinedload(OrderDB.user),
                joinedload(OrderDB.payment),
                selectinload(OrderDB.items),
            )
            .order_by(OrderDB.order_id.desc())
        )
        total_records = db.session.scalar(select(func.count(OrderDB.order_id)))
        if page > 1:
            orders_query = orders_query.offset((page - 1) * offset)
        orders_query = orders_query.limit(offset)

        orders_db = db.session.execute(orders_query).unique()
        adapter = TypeAdapter(list[OrderInDB])
    return OrderResponse(
        orders=adapter.validate_python(orders_db.scalars().all()),
        page=page,
        offset=offset,
        total_pages=math.ceil(total_records / offset) if total_records else 1,
        total_records=total_records if total_records else 0,
    )


def get_user_order(db: Session, user_id: int) -> list[OrderUserListResponse]:
    """Given order_id return Order with user data."""
    with db:
        order_query = (
            select(OrderDB)
            .options(
                joinedload(OrderDB.user),
                joinedload(OrderDB.payment),
                selectinload(OrderDB.items)
                .joinedload(OrderItemsDB.product),
            )
            .where(OrderDB.user_id == user_id)
            .order_by(OrderDB.order_id.desc())
        )
        orders = db.execute(order_query).scalars().unique().all()
        orders_obj = [
            OrderUserListResponse(
                order_id=order.order_id,
                cancelled_at=order.cancelled_at,
                cancelled_reason=order.cancelled_reason,
                freight=order.freight,
                order_date=order.order_date,
                order_status=order.order_status,
                tracking_number=order.tracking_number,
                products=[
                    ProductListOrderResponse(
                        product_id=item.product.product_id,
                        name=item.product.name,
                        uri=item.product.uri,
                        price=item.price,
                        quantity=item.quantity,
                    )
                    for item in order.items
                ],
            )
            for order in orders
        ]

        return [OrderUserListResponse.model_validate(order) for order in orders_obj]


def get_order(db: Session, order_id: int) -> OrderInDB:
    """Given order_id return Order with user data."""
    with db:
        order_query = (
            select(OrderDB)
            .options(
            joinedload(OrderDB.user),
            joinedload(OrderDB.payment),
            joinedload(OrderDB.items).joinedload(OrderItemsDB.product),
            joinedload(OrderDB.user).joinedload(UserDB.addresses.and_(
                AddressDB.address_id == (
                    select(func.max(AddressDB.address_id))
                    .where(AddressDB.user_id == OrderDB.user_id)
                ),
            )),
        )
            .where(OrderDB.order_id == order_id)
        )
        order = db.scalar(order_query)
        _order = OrderInDB.model_validate(order)
        last_address_subquery = (
            select(AddressDB)
            .where(AddressDB.user_id == order.user_id)
            .order_by(AddressDB.address_id.desc())
            .limit(1)
        )
        if order and order.user:
            last_address = db.scalar(last_address_subquery)
            if last_address:
                _order.user.addresses = [UserAddressInDB.model_validate(last_address)]
            else:
                _order.user.addresses = []
        return _order


def delete_order(order_id: int, *, cancel: CancelOrder, db) -> None:
    """Soft delete order."""
    with db:
        order_query = (
            select(OrderDB).options(
            joinedload(OrderDB.user),
            joinedload(OrderDB.payment),
            selectinload(OrderDB.items),
            )
            .where(OrderDB.order_id == order_id)
        )
        order = db.scalar(order_query)
        if not order:
            raise OrderNotFoundError
        order.order_status = PaymentStatus.CANCELLED
        order.checked = False
        order.cancelled_at = datetime.now(tz=UTC)
        order.cancelled_reason=cancel.cancel_reason
        db.add(order)
        db.commit()


def put_order(db: Session, order_data: OrderFullResponse, order_id):
    raise NotImplementedError


async def put_tracking_number(
    order_id: int,
    *,
    data: TrackingFullResponse,
    db,
    message,
) -> None:
    """Update tracking number."""
    async with db() as session:
        order = await session.get(OrderDB, order_id)
        order.tracking_number = data.tracking_number
        await session.commit()

    await message.broker.publish(
        {
            'mail_to': order.user.email,
            'order_id': order_id,
            'tracking_number': data.tracking_number,
        },
        queue=RabbitQueue('notification_tracking_number'),
    )


def checked_order(db: Session, order_id, check):
    ...


def create_order(db: Session, order_data: OrderSchema):
    ...


def get_category(db: Session) -> dict:
    """Get all categories."""
    categorys = None
    with db:
        categorys_query = select(CategoryDB)
        categorys = db.execute(categorys_query).scalars().all()

    category_list = []

    for category in categorys:
        category_list.append(CategoryInDB.model_validate(category))
    return {'category': category_list}


async def get_products_category(
    *,
    currency: CurrencyType,
    offset: int,
    page: int,
    path: str,
    db,
) -> ProductsResponse:
    """Get products and category."""
    async with db().begin() as transaction:
        category_query = select(CategoryDB).where(CategoryDB.path == path)
        category = await transaction.session.scalar(category_query)

        if not category:
            raise NotFoundCategoryError

        logger.info(category.path, category.category_id)

        products_query = (
            select(
                ProductDB.product_id,
                ProductDB.name,
                ProductDB.uri,
                ProductDB.price,
                ProductDB.active,
                ProductDB.direct_sales,
                ProductDB.description,
                ProductDB.image_path,
                ProductDB.installments_config,
                ProductDB.installments_list,
                ProductDB.discount,
                ProductDB.category_id,
                ProductDB.showcase,
                ProductDB.feature,
                ProductDB.show_discount,
                ProductDB.height,
                ProductDB.width,
                ProductDB.weight,
                ProductDB.length,
                ProductDB.diameter,
                ProductDB.sku,
                ProductDB.currency,
                func.coalesce(func.sum(InventoryDB.quantity), 0).label(
                    'quantity',
                ),
            )
            .where(ProductDB.category_id == category.category_id)
            .where(ProductDB.active.is_(True))
            .where(ProductDB.currency.like(currency))
            .outerjoin(
                InventoryDB,
                InventoryDB.product_id == ProductDB.product_id,
            )
            .outerjoin(
                CategoryDB,
                ProductDB.category_id == CategoryDB.category_id,
            )
            .group_by(ProductDB.product_id, CategoryDB.category_id)
        )
        total_records = await transaction.session.scalar(
            select(func.count(ProductDB.product_id)).where(
                ProductDB.category_id == category.category_id,
                ProductDB.active.is_(True),
            ),
        )
        if page > 1:
            products_query = products_query.offset((page - 1) * offset)
        products_query = products_query.limit(offset)
        products = await transaction.session.execute(products_query)
        adapter = TypeAdapter(list[ProductInDB])


    return ProductsResponse(
        total_records=total_records if total_records else 0,
        total_pages=math.ceil(total_records / offset) if total_records else 1,
        page=page,
        offset=offset,
        products=adapter.validate_python(products.all()),
    )


async def get_product_all(
    offset: int,
    page: int,
    currency: str,
    db,
) -> ProductsResponse:
    """Get all products."""
    async with db().begin() as transaction:
        products = (
            select(
                ProductDB.product_id,
                ProductDB.name,
                ProductDB.uri,
                ProductDB.price,
                ProductDB.active,
                ProductDB.direct_sales,
                ProductDB.description,
                ProductDB.image_path,
                ProductDB.installments_config,
                ProductDB.installments_list,
                ProductDB.discount,
                ProductDB.category_id,
                ProductDB.showcase,
                ProductDB.feature,
                ProductDB.show_discount,
                ProductDB.height,
                ProductDB.width,
                ProductDB.weight,
                ProductDB.length,
                ProductDB.diameter,
                ProductDB.sku,
                ProductDB.currency,
            )
            .outerjoin(
                CategoryDB,
                ProductDB.category_id == CategoryDB.category_id,
            )
            .where(ProductDB.active.is_(True))
            .where(ProductDB.currency.like(currency))
            .group_by(ProductDB.product_id, CategoryDB.category_id)
            .order_by(asc(ProductDB.product_id))
        )
        total_records = await transaction.session.scalar(
            select(func.count(ProductDB.product_id)),
        )
        if page > 1:
            products = products.offset((page - 1) * offset)
        products = products.limit(offset)
        products = await transaction.session.execute(products)
        adapter = TypeAdapter(list[ProductInDB])

    return ProductsResponse(
        total_records=total_records if total_records else 0,
        total_pages=math.ceil(total_records / offset) if total_records else 1,
        page=page,
        offset=offset,
        products=adapter.validate_python(products.all()),
    )


async def get_latest_products(
    *,
    currency: CurrencyType,
    offset: int,
    page: int,
    db,
) -> ProductsResponse:
    """Get latests products."""
    products = None
    async with db().begin() as transaction:
        products = (
            select(
                ProductDB.product_id,
                ProductDB.name,
                ProductDB.uri,
                ProductDB.price,
                ProductDB.active,
                ProductDB.direct_sales,
                ProductDB.description,
                ProductDB.image_path,
                ProductDB.installments_config,
                ProductDB.installments_list,
                ProductDB.discount,
                ProductDB.category_id,
                ProductDB.showcase,
                ProductDB.feature,
                ProductDB.show_discount,
                ProductDB.height,
                ProductDB.width,
                ProductDB.weight,
                ProductDB.length,
                ProductDB.diameter,
                ProductDB.sku,
                ProductDB.currency,
                func.coalesce(func.sum(InventoryDB.quantity), 0).label(
                    'quantity',
                ),
            )
            .outerjoin(
                InventoryDB,
                InventoryDB.product_id == ProductDB.product_id,
            )
            .outerjoin(
                CategoryDB,
                ProductDB.category_id == CategoryDB.category_id,
            )
            .where(ProductDB.active.is_(True))
            .where(ProductDB.currency.like(currency))
            .group_by(ProductDB.product_id, CategoryDB.category_id)
            .order_by(ProductDB.product_id.desc())
        )
        #!TODO precisa criar um campo created_at
        total_records = await transaction.session.scalar(
            select(func.count(ProductDB.product_id)),
        )
        if page > 1:
            products = products.offset((page - 1) * offset)
        products = products.limit(offset)
        products = await transaction.session.execute(products)
        adapter = TypeAdapter(list[ProductInDB])


    return ProductsResponse(
        total_records=total_records if total_records else 0,
        total_pages=math.ceil(total_records / offset) if total_records else 1,
        page=page,
        offset=offset,
        products=adapter.validate_python(products.all()),
    )


async def get_featured_products(
    *,
    currency: CurrencyType,
    offset: int,
    page: int,
    db,
) -> ProductsResponse:
    """Get Featured products."""
    async with db().begin() as transaction:
        products = (
            select(
                ProductDB.product_id,
                ProductDB.name,
                ProductDB.uri,
                ProductDB.price,
                ProductDB.active,
                ProductDB.direct_sales,
                ProductDB.description,
                ProductDB.image_path,
                ProductDB.installments_config,
                ProductDB.installments_list,
                ProductDB.discount,
                ProductDB.category_id,
                ProductDB.showcase,
                ProductDB.feature,
                ProductDB.show_discount,
                ProductDB.height,
                ProductDB.width,
                ProductDB.weight,
                ProductDB.length,
                ProductDB.diameter,
                ProductDB.sku,
                ProductDB.currency,
            )
            .options(lazyload('*'))
            .join(
                CategoryDB,
                ProductDB.category_id == CategoryDB.category_id,
            )
            .where(
                ProductDB.feature.is_(True),
                ProductDB.active.is_(True),
            )
            .where(ProductDB.currency.like(currency))
            .group_by(ProductDB.product_id, CategoryDB.category_id)
        )
        total_records = await transaction.session.scalar(
            select(func.count(ProductDB.product_id)),
        )
        if page > 1:
            products = products.offset((page - 1) * offset)
        products = products.limit(offset)

        products = await transaction.session.execute(products)
        adapter = TypeAdapter(list[ProductInDB])

    return ProductsResponse(
        total_records=total_records if total_records else 0,
        total_pages=math.ceil(total_records / offset) if total_records else 1,
        page=page,
        offset=offset,
        products=adapter.validate_python(products.all()),
    )


async def search_products(
    currency: CurrencyType,
    search: str,
    offset: int,
    page: int,
    db,
) -> ProductsResponse:
    """Search Products."""
    products = None
    async with db().begin() as transaction:
        products = (
            select(
                ProductDB.product_id,
                ProductDB.name,
                ProductDB.uri,
                ProductDB.price,
                ProductDB.active,
                ProductDB.direct_sales,
                ProductDB.description,
                ProductDB.image_path,
                ProductDB.installments_config,
                ProductDB.installments_list,
                ProductDB.discount,
                ProductDB.category_id,
                ProductDB.showcase,
                ProductDB.feature,
                ProductDB.show_discount,
                ProductDB.height,
                ProductDB.width,
                ProductDB.weight,
                ProductDB.length,
                ProductDB.diameter,
                ProductDB.sku,
                ProductDB.currency,
                func.coalesce(func.sum(InventoryDB.quantity), 0).label(
                    'quantity',
                ),
            )
            .options(lazyload('*'))
            .outerjoin(
                CategoryDB,
                ProductDB.category_id == CategoryDB.category_id,
            )
            .outerjoin(
                InventoryDB,
                InventoryDB.product_id == ProductDB.product_id,
            )
            .where(
                ProductDB.name.ilike(f'%{search}%'),
            )
            .where(ProductDB.currency.like(currency))
            .group_by(ProductDB.product_id, CategoryDB.category_id)
        )
        total_records = await transaction.session.scalar(
            select(func.count(ProductDB.product_id)).where(
                ProductDB.name.ilike(f'%{search}%'),
            ),
        )
        if page > 1:
            products = products.offset((page - 1) * offset)
        products = products.limit(offset)
        products = await transaction.session.execute(products)
        adapter = TypeAdapter(list[ProductInDB])

    return ProductsResponse(
        total_records=total_records if total_records else 0,
        total_pages=math.ceil(total_records / offset) if total_records else 1,
        page=page,
        offset=offset,
        products=adapter.validate_python(products.all()),
    )


async def update_pending_orders(db=get_async_session):
    """Get all peding order and update."""
    async with db().begin() as session:
        orders = await repository_order.get_order_by_status(
            OrderStatus.PAYMENT_PENDING.value,
            transaction=session,
        )
        for order in orders.unique().all():
            logger.debug('Order search start')
            logger.debug(order.order_id)

            payment = await repository_payment.get_payment_by_order_id(
                order.order_id,
                transaction=session.begin(),
            )
            if not payment:
                order.order_status = OrderStatus.PAYMENT_CANCELLED
                session.add(order)
                continue

            logger.debug(f'{order.order_id} - {payment.status}')
            if payment.status not in ('approved', 'authorized', 'cancelled'):
                continue
            logger.debug('update order status')
            logger.debug(f'Add old status in Order {order.order_status}')
            order.order_status = OrderStatus.PAYMENT_PAID
            if payment.status == 'cancelled':
                order.order_status = OrderStatus.PAYMENT_CANCELLED
            logger.debug(f'Add new status in Order {order.order_status}')
            session.add(order)

            await session.flush()
        logger.debug('commit all transactions')
        await session.commit()
