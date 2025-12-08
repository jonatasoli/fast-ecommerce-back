from collections.abc import Callable
from fastapi import UploadFile
from loguru import logger
from pydantic import TypeAdapter

from app.entities.product import (
    ProductCreate,
    ProductInDBResponse,
    ProductNotFoundError,
    ProductPatchRequest,
    UploadedMediaInDBResponse,
)
from app.infra import file_upload
from app.infra.constants import MediaType
from app.infra.models import MediaGalleryDB, UploadedMediaDB
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
    """Upload single image for product."""
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


async def upload_media_gallery(
    product_id: int,
    *,
    media_type: MediaType,
    media: UploadFile,
    order: int,
    db,
) -> str:
    """Upload media Galery."""
    media_path = None
    if media_type == MediaType.photo.value:
        media_path = file_upload.optimize_image(media)
    elif media_type == MediaType.video.value:
        media_path = await file_upload.upload_video(media)
    async with db().begin() as transaction:
        db_media_upload = UploadedMediaDB(
            type=media_type,
            uri=media_path,
            order=order,
        )
        transaction.session.add(db_media_upload)
        await transaction.session.flush()
        logger.debug(f'Media id {db_media_upload.media_id}')
        db_media_gallery = MediaGalleryDB(
            media_id=db_media_upload.media_id,
            product_id=product_id,
        )
        transaction.session.add(db_media_gallery)
        await transaction.session.flush()
        logger.debug(f'Media Gallery id {db_media_gallery.media_gallery_id}')
        logger.debug(f'Media id {db_media_gallery.media_id}')
        await transaction.session.commit()
    return media_path


async def delete_media_gallery(
    product_id: int,
    *,
    media_id: int,
    db,
) -> None:
    """Delete image galery."""
    async with db().begin() as transaction:
        gallery_db = await repository.get_gallery_by_media_id(
            media_id,
            product_id=product_id,
            transaction=transaction,
        )
        upload_media_db = await repository.get_media_by_media_id(
            media_id,
            product_id=product_id,
            transaction=transaction,
        )
        await transaction.session.delete(gallery_db)
        await transaction.session.delete(upload_media_db)
        await transaction.session.commit()


async def get_media_gallery(uri: str, *, db) -> list[UploadedMediaInDBResponse]:
    """Get media gallery."""
    async with db().begin() as transaction:
        product_db = await repository.get_product_by_uri(uri, transaction=transaction)
        media_db = await repository.get_media_by_product_id(
            product_db.product_id,
            transaction=transaction,
        )
        adapter = TypeAdapter(list[UploadedMediaInDBResponse])
        return adapter.validate_python(media_db.all())
