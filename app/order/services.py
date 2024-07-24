import json
import math
from typing import Any, List

from fastapi import HTTPException, status
from loguru import logger
from pydantic import TypeAdapter
from sqlalchemy import func, select
from sqlalchemy.orm import Session, aliased
from app.product import repository

from app.entities.order import OrderInDB, OrderResponse
from app.entities.product import (
    ProductCategoryInDB,
    ProductCreate,
    ProductInDB,
    ProductInDBResponse,
    ProductPatchRequest,
    ProductsResponse,
)
from app.infra.file_upload import optimize_image
from app.infra.models import (
    CategoryDB,
    ImageGalleryDB,
    InventoryDB,
    ProductDB,
    OrderDB,
    OrderItemsDB,
)
from app.user.services import verify_admin
from schemas.order_schema import (
    CategoryInDB,
    ImageGalleryResponse,
    OrderFullResponse,
    OrderSchema,
    TrackingFullResponse,
    OrderUserListResponse,
    ProductListOrderResponse,
)


def get_product(db: Session, uri: str) -> ProductInDB | None:
    """Return specific product."""
    with db:
        category_alias = aliased(CategoryDB)
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
                category_alias.category_id.label('category_id_1'),
                category_alias.name.label('name_1'),
                category_alias.path,
                category_alias.menu,
                category_alias.showcase.label('showcase_1'),
                category_alias.image_path.label('image_path_1'),
            )
            .where(ProductDB.uri == uri)
            .where(ProductDB.active.is_(True))
            .outerjoin(
                InventoryDB,
                InventoryDB.product_id == ProductDB.product_id,
            )
            .outerjoin(
                category_alias,
                ProductDB.category_id == category_alias.category_id,
            )
            .group_by(ProductDB.product_id, category_alias.category_id)
        )
        result = db.execute(query_product)
        column_names = result.keys()
        product = result.first()
        if not product:
            return None
        product_dict = dict(zip(column_names, product))
        if 'category_id_1' in product_dict:
            product_dict['category'] = {
                'category_id': product_dict['category_id_1'],
                'name': product_dict['name_1'],
                'path': product_dict['path'],
                'menu': product_dict['menu'],
                'showcase': product_dict['showcase_1'],
                'image_path': product_dict['image_path_1'],
            }
            del product_dict['category_id_1']
            del product_dict['name_1']
            del product_dict['path']
            del product_dict['menu']
            del product_dict['showcase_1']
            del product_dict['image_path_1']
        if product_dict:
            return ProductInDB.model_validate(product_dict)
        return None


def create_product(
    product_data: ProductCreate,
    *,
    token,
    verify_admin = verify_admin,
    db: Session,
) -> ProductInDBResponse:
    """Create new product."""
    verify_admin(token, db=db)
    db_product = ProductDB(**product_data.model_dump(exclude={'description'}))
    db_product.description = json.dumps(product_data.description)
    try:
        with db:
            db.add(db_product)
            db.commit()
            return ProductInDBResponse.model_validate(db_product)
    except Exception as e:
        logger.error(e)
        raise


def update_product(product: ProductDB, product_data: dict) -> ProductDB:
    """Update product by id."""
    for key, value in product_data.items():
        setattr(product, key, value)
    return product


def patch_product(
    product_id,
    *,
    product_data: ProductPatchRequest,
    db,
) -> None:
    """Update Product."""
    values = product_data.model_dump(exclude_none=True)
    product = get_product_by_id(db, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Product not found',
        )
    with db:
        update_product(product, values)
        db.commit()


def delete_product(db: Session, product_id: int) -> None:
    """Remove Product."""
    with db:
        db.execute(
            select(ProductDB).where(ProductDB.product_id == product_id),
        ).delete()
        db.commit()


def upload_image_gallery(
    product_id: int,
    db: Session,
    imageGallery: Any,
) -> str:
    """Upload Image Galery."""
    image_path = optimize_image.optimize_image(imageGallery)
    with db:
        db_image_gallery = ImageGalleryDB(
            url=image_path,
            product_id=product_id,
        )
        db.add(db_image_gallery)
        db.commit()
    return image_path


def delete_image_gallery(id: int, db: Session) -> None:
    """Delete image galery."""
    with db:
        db.execute(
            select(ImageGalleryDB).where(ImageGalleryDB.id == id),
        ).delete()
        db.commit()


def get_images_gallery(db: Session, uri: str) -> dict:
    """Get image gallery."""
    with db:
        product_id_query = select(ProductDB).where(ProductDB.uri == uri)
        product_id = db.execute(product_id_query).scalars().first()
        images_query = select.query(ImageGalleryDB).where(
            ImageGalleryDB.product_id == product_id.id,
        )
        images = db.execute(images_query).scalars().all()
        images_list = []

        for image in images:
            images_list.append(ImageGalleryResponse.from_orm(image))

        if images:
            return {'images': images_list}
        return {'images': []}


def get_showcase(db: Session) -> list:
    """Get Products showcase."""
    with db:
        showcases_query = (
            select(ProductDB)
            .where(ProductDB.showcase == True)
            .where(ProductDB.active == True)
        )
        showcases = db.execute(showcases_query).scalars().all()

        return [
            ProductCategoryInDB.model_validate(showcase)
            for showcase in showcases
        ]


def get_installments(product_id: int, *, db: Session) -> int:
    """Get installments."""
    with db:
        _product_config_query = select(ProductDB).where(
            ProductDB.product_id == product_id,
        )
        product = db.scalar(_product_config_query)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Product not found',
            )
        _total_amount = 0
        _total_amount_fee = 0
        _installments = []

        for n in range(1, 13):
            if n <= 3:
                _installment = (product.price / n) / 100
                _installments.append(
                    {
                        'name': f'{n} x R${round(_installment, 2)}',
                        'value': f'{n}',
                    },
                )
                logger.debug(f'Parcela sem juros {_installment}')
            else:
                _total_amount_fee = int(product.price) * (1 + (0.0199 * n))
                _installment = (_total_amount_fee / n) / 100
                _installments.append(
                    {
                        'name': f'{n} x R${round(_installment, 2)}',
                        'value': f'{n}',
                    },
                )
                logger.debug(f'Parcela com juros {_installment}')

        logger.debug(f'array de parcelas {_installments}')
        return _installments


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
    with db().begin() as db:
        orders_query = (
            select(OrderDB)
            .order_by(OrderDB.order_id.desc())
        )
        total_records = db.session.scalar(select(func.count(OrderDB.order_id)))
        if page > 1:
            orders_query = orders_query.offset((page - 1) * offset)
        orders_query = orders_query.limit(offset)

        orders_db = db.session.execute(orders_query)
        adapter = TypeAdapter(List[OrderInDB])
    return OrderResponse(
        orders=adapter.validate_python(orders_db.scalars().all()),
        page=page,
        offset=offset,
        total_pages=math.ceil(total_records / offset) if total_records else 1,
        total_records=total_records if total_records else 0,
    )


def get_order(db: Session, user_id: int) -> list[OrderUserListResponse]:
    """Given order_id return Order with user data."""
    with db:
        order_query = (
            select(OrderDB)
            .where(OrderDB.user_id == user_id)
            .order_by(OrderDB.order_id.desc())
        )
        orders = db.execute(order_query).scalars().all()
        orders_obj = []
        for order in orders:
            items_query = (
                select(OrderItemsDB)
                .join(
                    ProductDB,
                    OrderItemsDB.product_id == ProductDB.product_id,
                )
                .where(OrderItemsDB.order_id == order.order_id)
            )
            items = db.execute(items_query).scalars().all()
            products_list = [
                ProductListOrderResponse(
                    product_id=item.product_id,
                    name=item.product.name,
                    uri=item.product.uri,
                    price=item.price,
                    quantity=item.quantity,
                )
                for item in items
            ]

            orders_obj.append(
                OrderUserListResponse(
                    order_id=order.order_id,
                    cancelled_at=order.cancelled_at,
                    cancelled_reason=order.cancelled_reason,
                    freight=order.freight,
                    order_date=order.order_date,
                    order_status=order.order_status,
                    tracking_number=order.tracking_number,
                    products=products_list,
                ),
            )
        return [
            OrderUserListResponse.model_validate(order) for order in orders_obj
        ]


def get_order_users(db: Session, id):
    ...


def put_order(db: Session, order_data: OrderFullResponse, id):
    ...


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


def checked_order(db: Session, id, check):
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
        category_list.append(CategoryInDB.from_orm(category))
    return {'category': category_list}


class NotFoundCategoryException(Exception):
    """Not Found Category Exception."""


def get_products_category(
    *,
    offset: int,
    page: int,
    path: str,
    db: Session,
) -> ProductsResponse:
    """Get products and category."""
    products = None
    products_category = []
    with db:
        category_query = select(CategoryDB).where(CategoryDB.path == path)
        category = db.scalar(category_query)

        if not category:
            raise NotFoundCategoryException

        logger.info(category.path, category.category_id)

        category_alias = aliased(CategoryDB)
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
                category_alias.category_id.label('category_id_1'),
                category_alias.name.label('name_1'),
                category_alias.path,
                category_alias.menu,
                category_alias.showcase.label('showcase_1'),
                category_alias.image_path.label('image_path_1'),
            )
            .where(ProductDB.category_id == category.category_id)
            .where(ProductDB.active == True)
            .outerjoin(
                InventoryDB,
                InventoryDB.product_id == ProductDB.product_id,
            )
            .outerjoin(
                category_alias,
                ProductDB.category_id == category_alias.category_id,
            )
            .group_by(ProductDB.product_id, category_alias.category_id)
        )
        total_records = db.scalar(
            select(func.count(ProductDB.product_id)).where(
                ProductDB.category_id == category.category_id,
            ),
        )
        if page > 1:
            products_query = products_query.offset((page - 1) * offset)
        products_query = products_query.limit(offset)

        products = db.execute(products_query)

        keys = products.keys()
        for product in products:
            product_dict = dict(zip(keys, product))
            if 'category_id_1' in product_dict:
                product_dict['category'] = {
                    'category_id': product_dict['category_id_1'],
                    'name': product_dict['name_1'],
                    'path': product_dict['path'],
                    'menu': product_dict['menu'],
                    'showcase': product_dict['showcase_1'],
                    'image_path': product_dict['image_path_1'],
                }
                del product_dict['category_id_1']
                del product_dict['name_1']
                del product_dict['path']
                del product_dict['menu']
                del product_dict['showcase_1']
                del product_dict['image_path_1']
            products_category.append(
                ProductCategoryInDB.model_validate(product_dict),
            )

    return ProductsResponse(
        total_records=total_records if total_records else 0,
        total_pages=math.ceil(total_records / offset) if total_records else 1,
        page=page,
        offset=offset,
        products=products_category,
    )


async def get_product_all(offset: int, page: int, db: Session) -> ProductsResponse:
    """Get all products."""
    async with db().begin() as transaction:
        products = (
            select(ProductDB)
            .where(ProductDB.active == True)
            .order_by(ProductDB.product_id.asc())
        )
        total_records = await transaction.session.scalar(select(func.count(ProductDB.product_id)))
        if page > 1:
            products = products.offset((page - 1) * offset)
        products = products.limit(offset)

        result = await transaction.session.execute(products)
        adapter = TypeAdapter(List[ProductCategoryInDB])
        products_list = result.scalars().all()
        products_list = adapter.validate_python(products_list)

    return ProductsResponse(
        total_records=total_records if total_records else 0,
        total_pages=math.ceil(total_records / offset) if total_records else 1,
        page=page,
        offset=offset,
        products=products_list,
    )


def get_latest_products(
    offset: int,
    page: int,
    db: Session,
) -> ProductsResponse:
    """Get latests products."""
    products = None
    with db:
        category_alias = aliased(CategoryDB)
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
                category_alias.category_id.label('category_id_1'),
                category_alias.name.label('name_1'),
                category_alias.path,
                category_alias.menu,
                category_alias.showcase.label('showcase_1'),
                category_alias.image_path.label('image_path_1'),
            )
            .outerjoin(
                InventoryDB,
                InventoryDB.product_id == ProductDB.product_id,
            )
            .outerjoin(
                category_alias,
                ProductDB.category_id == category_alias.category_id,
            )
            .where(ProductDB.active == True)
            .group_by(ProductDB.product_id, category_alias.category_id)
        )
        total_records = db.scalar(select(func.count(ProductDB.product_id)))
        if page > 1:
            products = products.offset((page - 1) * offset)
        products = products.limit(offset)
        products = products.order_by(ProductDB.product_id.desc())

        result = db.execute(products)
        column_names = result.keys()
        products = result.fetchall()
    products_list = []

    for product in products:
        product_dict = dict(zip(column_names, product))
        if 'category_id_1' in product_dict:
            product_dict['category'] = {
                'category_id': product_dict['category_id_1'],
                'name': product_dict['name_1'],
                'path': product_dict['path'],
                'menu': product_dict['menu'],
                'showcase': product_dict['showcase_1'],
                'image_path': product_dict['image_path_1'],
            }
            del product_dict['category_id_1']
            del product_dict['name_1']
            del product_dict['path']
            del product_dict['menu']
            del product_dict['showcase_1']
            del product_dict['image_path_1']
        products_list.append(ProductCategoryInDB.model_validate(product_dict))

    return ProductsResponse(
        total_records=total_records if total_records else 0,
        total_pages=math.ceil(total_records / offset) if total_records else 1,
        page=page,
        offset=offset,
        products=products_list,
    )


def get_featured_products(
    offset: int,
    page: int,
    db: Session,
) -> ProductsResponse:
    """Get Featured products."""
    products = None
    with db:
        products = select(ProductDB).where(
            ProductDB.feature == True,
            ProductDB.active == True,
        )
        total_records = db.scalar(select(func.count(ProductDB.product_id)))
        if page > 1:
            products = products.offset((page - 1) * offset)
        products = products.limit(offset)

        products = db.scalars(products).all()
    products_list = []

    for product in products:
        products_list.append(ProductCategoryInDB.model_validate(product))

    return ProductsResponse(
        total_records=total_records if total_records else 0,
        total_pages=math.ceil(total_records / offset) if total_records else 1,
        page=page,
        offset=offset,
        products=products_list,
    )


def search_products(
    search: str,
    offset: int,
    page: int,
    db: Session,
) -> ProductsResponse:
    """Search Products."""
    products = None
    with (db):
        category_alias = aliased(CategoryDB)
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
                category_alias.category_id.label('category_id_1'),
                category_alias.name.label('name_1'),
                category_alias.path,
                category_alias.menu,
                category_alias.showcase.label('showcase_1'),
                category_alias.image_path.label('image_path_1'),
            )
            .where(
                ProductDB.name.ilike(f'%{search}%'),
            )
            .outerjoin(
                InventoryDB,
                InventoryDB.product_id == ProductDB.product_id,
            )
            .outerjoin(
                category_alias,
                ProductDB.category_id == category_alias.category_id,
            )
            .group_by(ProductDB.product_id, category_alias.category_id)
        )
        total_records = db.scalar(
            select(func.count(ProductDB.product_id)).where(
                ProductDB.name.ilike(f'%{search}%'),
            ),
        )
        if page > 1:
            products = products.offset((page - 1) * offset)
        products = products.limit(offset)
        products = db.execute(products)
    products_list = []

    keys = products.keys()
    for product in products:
        product_dict = dict(zip(keys, product))
        if 'category_id_1' in product_dict:
            product_dict['category'] = {
                'category_id': product_dict['category_id_1'],
                'name': product_dict['name_1'],
                'path': product_dict['path'],
                'menu': product_dict['menu'],
                'showcase': product_dict['showcase_1'],
                'image_path': product_dict['image_path_1'],
            }
            del product_dict['category_id_1']
            del product_dict['name_1']
            del product_dict['path']
            del product_dict['menu']
            del product_dict['showcase_1']
            del product_dict['image_path_1']
        products_list.append(ProductCategoryInDB.model_validate(product_dict))

    return ProductsResponse(
        total_records=total_records if total_records else 0,
        total_pages=math.ceil(total_records / offset) if total_records else 1,
        page=page,
        offset=offset,
        products=products_list,
    )
