from typing import Any
from collections.abc import Callable
from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.entities.order import ImageGalleryResponse
from app.entities.product import (
    ProductCreate,
    ProductInDBResponse,
    ProductNotFoundError,
    ProductPatchRequest,
)
from app.infra import file_upload
from app.infra.models import ImageGalleryDB, ProductDB
from app.product import repository
from app.user.services import verify_admin


def product_not_found_exception():
    """Product not found."""
    raise ProductNotFoundError

async def upload_image(
    product_id: int,
    *,
    db,
    image: UploadFile,
    image_client: Callable = file_upload,
) -> str:
    """Upload image."""
    image_path = image_client.optimize_image(image)
    async with db().begin() as transaction:
        db_product = await repository.get_product_by_id(
            product_id,
            transaction=transaction,
        )
        db_product.image_path = image_path
        await transaction.session.commit()
    return db_product.image_path

async def get_inventory(token, *, page, offset, db, verify_admin=verify_admin):
    """Get products inventory."""
    await verify_admin(token, db=db)
    async with db().begin() as transaction:
        return await repository.get_inventory(transaction, page=page, offset=offset)

async def get_inventory_name(path, *, currency, page, offset, db):
    """Get products inventory."""
    async with db().begin() as transaction:
        return await repository.get_inventory(
            transaction,
            currency=currency,
            name=path,
            page=page,
            offset=offset,
    )

async def inventory_transaction(product_id: int, *, inventory, token, db):
    """Add product transaction."""
    _ = token
    async with db().begin() as transaction:
        return await repository.add_inventory_transaction(
            product_id,
            inventory,
            transaction,
        )


async def create_product(
    product_data: ProductCreate,
    *,
    db,
) -> ProductInDBResponse:
    """Create new product."""
    async with db().begin() as transaction:
        db_product = await repository.create_product(product_data, transaction)
        return ProductInDBResponse.model_validate(db_product)


async def update_product(
    product_id,
    *,
    update_data: ProductPatchRequest,
    db,
) -> None:
    """Update Product."""
    columns_update = update_data.model_dump(exclude_none=True)
    async with db().begin() as transaction:
        product_db = await repository.get_product_by_id(
            product_id,
            transaction=transaction,
        )
        if not product_db:
            product_not_found_exception()
        for field, value in columns_update.items():
            if value is not None:
                setattr(product_db, field, value)
        await transaction.commit()


async def delete_product(product_id: int, db) -> None:
    """Remove Product."""
    with db().begin() as transaction:
        await repository.delete_product(product_id, transaction=transaction)
        transaction.commit()


def upload_image_gallery(
    product_id: int,
    *,
    db: Session,
    media: Any,
) -> str:
    """Upload Image Galery."""
    image_path = file_upload.optimize_image(media)
    with db:
        db_image_gallery = ImageGalleryDB(
            url=image_path,
            product_id=product_id,
        )
        db.add(db_image_gallery)
        db.commit()
    return image_path


async def delete_image_gallery(product_id: int, db) -> None:
    """Delete image galery."""
    with db:
        db.execute(
            select(ImageGalleryDB).where(ImageGalleryDB.id == product_id),
        ).delete()
        db.commit()


def get_images_gallery(db: Session, uri: str) -> dict:
    """Get image gallery."""
    with db:
        product_id_query = select(ProductDB).where(ProductDB.uri == uri)
        product_id = db.execute(product_id_query).scalars().first()
        images_query = select(ImageGalleryDB).where(
            ImageGalleryDB.product_id == product_id.product_id,
        )
        images = db.execute(images_query).scalars().all()
        images_list = []

        for image in images:
            images_list.append(ImageGalleryResponse.from_orm(image))

        if images:
            return {'images': images_list}
        return {'images': []}


