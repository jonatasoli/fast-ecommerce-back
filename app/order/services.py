import json
import math
from typing import Any

from fastapi import HTTPException, status
from loguru import logger
from sqlalchemy import func, select
from sqlalchemy.orm import Session, aliased

from app.entities.product import (
    ProductCategoryInDB,
    ProductInDB,
    ProductsResponse,
)
from app.infra.models import (
    CategoryDB,
    ImageGalleryDB,
    InventoryDB,
    ProductDB,
    OrderDB,
    OrderItemsDB,
)
from app.infra.optimize_image import optimize_image
from schemas.order_schema import (
    CategoryInDB,
    ImageGalleryResponse,
    OrderFullResponse,
    OrderSchema,
    ProductSchema,
    ProductSchemaResponse,
    TrackingFullResponse,
    OrderUserListResponse,
    ProductListOrderResponse,
    ProductPatchRequest,
    ProductFullResponse,
)


def get_product(db: Session, uri) -> ProductInDB | None:
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
    db: Session,
    product_data: ProductSchema,
) -> bool | ProductSchemaResponse:
    """Create new product."""
    db_product = ProductDB(**product_data.model_dump(exclude={'description'}))
    db_product.description = json.dumps(product_data.description)
    try:
        with db:
            db.add(db_product)
            db.commit()
            return ProductSchemaResponse.model_validate(db_product)
    except Exception as e:
        logger.error(e)
        return False


def update_product(product: ProductDB, product_data: dict) -> ProductDB:
    for key, value in product_data.items():
        setattr(product, key, value)
    return product


def patch_product(
    db: Session, id, product_data: ProductPatchRequest
) -> ProductFullResponse:
    """Update Product."""
    values = product_data.model_dump(exclude_none=True)
    product = get_product_by_id(db, id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Product not found',
        )
    with db:
        update_product(product, values)
        db.commit()
        return ProductFullResponse.model_validate(product)


def delete_product(db: Session, id: int) -> None:
    """Remove Product."""
    with db:
        db.execute(
            select(ProductDB).where(ProductDB.id == id).delete(),
        ).delete()
        db.commit()


def upload_image(db: Session, product_id: int, image: Any) -> str:
    """Upload image."""
    image_path = optimize_image.optimize_image(image)
    with db:
        db_product = (
            db.query(ProductDB).filter(ProductDB.id == product_id).first()
        )
        db_product.image_path = image_path
        db.commit()
    return image_path


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
        showcases_query = select(ProductDB).where(ProductDB.showcase == True)
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


def get_product_by_id(db: Session, id: int) -> ProductDB | None:
    return db.query(ProductDB).filter(ProductDB.product_id == id).first()


def get_orders_paid(db: Session, dates=None, status=None, user_id=None):
    """Get Orders Paid."""
    ...


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


def put_trancking_number(db: Session, data: TrackingFullResponse, id):
    ...


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

        products_query = select(ProductDB).where(
            ProductDB.category_id == category.category_id,
        )
        total_records = db.scalar(
            select(func.count(ProductDB.product_id)).where(
                ProductDB.category_id == category.category_id,
            ),
        )
        if page > 1:
            products_query = products_query.offset((page - 1) * offset)
        products_query = products_query.limit(offset)

        products = db.scalars(products_query)

        for product in products:
            products_category.append(
                ProductCategoryInDB.model_validate(product),
            )

    return ProductsResponse(
        total_records=total_records if total_records else 0,
        total_pages=math.ceil(total_records / offset) if total_records else 1,
        page=page,
        offset=offset,
        products=products_category,
    )


def get_product_all(offset: int, page: int, db: Session) -> ProductsResponse:
    """Get all products."""
    products = None
    total_records = 0
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
            .group_by(ProductDB.product_id, category_alias.category_id)
        )
        total_records = db.scalar(select(func.count(ProductDB.product_id)))
        if page > 1:
            products = products.offset((page - 1) * offset)
        products = products.limit(offset)

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
        products = select(ProductDB).where(ProductDB.feature == True)
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
