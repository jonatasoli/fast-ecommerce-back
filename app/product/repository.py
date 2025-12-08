import json
import math
from loguru import logger
from pydantic import TypeAdapter
from sqlalchemy import delete, select
from sqlalchemy.orm import lazyload
from sqlalchemy import func

from app.entities.product import (
    InventoryResponse,
    InventoryTransaction,
    ProductCreate,
    ProductInDB,
    ProductNotCreatedError,
    ProductNotFoundError,
)
from app.infra.models import (
    CategoryDB,
    InventoryDB,
    MediaGalleryDB,
    ProductDB,
    UploadedMediaDB,
)


def create_product_not_found_exception() -> ProductNotCreatedError:
    """Shoud raise exception if product is not created."""
    raise ProductNotCreatedError


async def get_product_by_id(product_id: int, *, transaction):
    """Get product by id."""
    return await transaction.session.scalar(
        select(ProductDB).where(ProductDB.product_id == product_id),
    )


async def get_product_by_uri(uri: str, *, transaction):
    """Get product by uri."""
    product_db = await transaction.session.scalar(
        select(ProductDB).where(ProductDB.uri == uri),
    )
    if not product_db:
        raise ProductNotFoundError
    return product_db


async def get_media_by_product_id(
    product_id: int,
    *,
    transaction,
) -> list[UploadedMediaDB]:
    """Get all products in Media Gallery."""
    query = (
        select(UploadedMediaDB)
        .join(
            MediaGalleryDB,
            MediaGalleryDB.media_id == UploadedMediaDB.media_id,
        )
        .where(
            MediaGalleryDB.product_id == product_id,
            UploadedMediaDB.active.is_(True),
        )
    )
    return await transaction.session.scalars(query)


async def get_media_by_media_id(
    media_id: int,
    *,
    product_id,
    transaction,
) -> MediaGalleryDB:
    """Get all products in Media Gallery."""
    query = (
        select(UploadedMediaDB)
        .join(
            MediaGalleryDB,
            MediaGalleryDB.media_id == UploadedMediaDB.media_id,
        )
        .where(
            UploadedMediaDB.media_id == media_id,
            MediaGalleryDB.product_id == product_id,
        )
    )
    return await transaction.session.scalar(query)


async def get_gallery_by_media_id(
    media_id: int,
    *,
    product_id,
    transaction,
) -> list[UploadedMediaDB]:
    """Get all products in Media Gallery."""
    query = select(MediaGalleryDB).where(
        MediaGalleryDB.media_id == media_id,
        MediaGalleryDB.product_id == product_id,
    )
    return await transaction.session.scalar(query)


async def get_inventory(transaction, *, page, offset, currency=None, name=None):
    """Get inventory products."""
    _ = currency
    quantity_query = (
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
    if not name:
        total_records_query = select(
            func.count(ProductDB.product_id),
        )
    else:
        total_records_query = select(
            func.count(ProductDB.product_id),
        ).where(ProductDB.name.ilike(f'%{name}%'))
        quantity_query = quantity_query.where(ProductDB.name.ilike(f'%{name}%'))
    total_records = await transaction.session.scalar(
        total_records_query,
    )
    if page > 1:
        quantity_query = quantity_query.offset((page - 1) * offset)
    quantity_query = quantity_query.limit(offset)

    products_db = await transaction.session.execute(quantity_query)
    adapter = TypeAdapter(list[ProductInDB])
    return InventoryResponse(
        inventory=adapter.validate_python(products_db.all()),
        page=page,
        offset=offset,
        total_pages=math.ceil(total_records / offset) if total_records else 1,
        total_records=total_records if total_records else 0,
    )


async def add_inventory_transaction(
    product_id: int,
    inventory: InventoryTransaction,
    transaction,
) -> InventoryDB:
    """Add inventory in InventoryDB."""
    inventorydb = InventoryDB(
        product_id=product_id,
        quantity=inventory.quantity,
        operation=inventory.operation,
    )
    transaction.session.add(inventorydb)
    await transaction.session.commit()
    return inventorydb


async def create_product(
    product_data: ProductCreate,
    transaction,
):
    """Create a new product in DB."""
    db_product = ProductDB(**product_data.model_dump(exclude={'description'}))
    db_product.description = json.dumps(product_data.description)
    try:
        transaction.session.add(db_product)
        await transaction.session.commit()
        if not db_product:
            create_product_not_found_exception()
    except Exception as e:
        logger.error(e)
        raise
    else:
        return db_product


async def delete_product(
    product_id: int,
    *,
    transaction,
) -> None:
    """Delete product."""
    async with transaction:
        return await transaction.scalar(
            delete(ProductDB).where(ProductDB.product_id == product_id),
        )
