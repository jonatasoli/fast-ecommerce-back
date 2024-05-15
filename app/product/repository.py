from typing import List
from pydantic import TypeAdapter
from sqlalchemy import select
from sqlalchemy.orm import Session, lazyload
from sqlalchemy import func

from app.entities.product import ProductInDB
from app.infra.models import CategoryDB, InventoryDB, ProductDB


def get_product_by_id(product_id: int, *, db: Session):
    """Get product by id."""
    return db.scalar(
        select(ProductDB).where(ProductDB.product_id == product_id),
    )


async def get_inventory(transaction):
    """Get inventory products."""
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
    )
    products_db = await transaction.execute(quantity_query)
    adapter = TypeAdapter(List[ProductInDB])
    return adapter.validate_python(products_db.all())

