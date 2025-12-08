from collections.abc import Callable
from typing import Any

from fastapi import UploadFile
from loguru import logger
from sqlalchemy import delete, select

from app.catalog import repository as catalog_repository
from app.entities.catalog import (
    Categories,
    Category,
    CategoryCreate,
    CategoryResponse,
    CategoryUpdate,
)
from app.entities.category import CategoryMediaNotFoundError, CategoryNotFoundError
from app.infra import file_upload
from app.infra.constants import MediaType
from app.infra.models import CategoryMediaGalleryDB, UploadedMediaDB


async def get_categories_by_filter(
    *,
    menu: bool,
    showcase: bool,
    db: Any,
) -> Categories:
    """Must return all categories in catalog."""
    categories = []
    async with db().begin() as transaction:
        categories_db = await catalog_repository.get_categories(
            menu=menu,
            showcase=showcase,
            transaction=transaction,
        )
    for category in categories_db:
        categories.append(Category.model_validate(category))
    return Categories(categories=categories)


async def get_category_by_id(
    category_id: int,
    *,
    db: Any,
) -> CategoryResponse | None:
    """Get category by ID."""
    async with db().begin() as transaction:
        db_category = await catalog_repository.get_category_by_id(
            category_id,
            transaction=transaction,
        )
        if not db_category:
            return None
        return CategoryResponse.model_validate(db_category)


async def create_category(
    category_data: CategoryCreate,
    *,
    db: Any,
) -> CategoryResponse:
    """Create new category."""
    async with db().begin() as transaction:
        db_category = await catalog_repository.create_category(
            category_data.model_dump(),
            transaction=transaction,
        )
        await transaction.session.commit()
        return CategoryResponse.model_validate(db_category)


async def update_category(
    category_id: int,
    category_data: CategoryUpdate,
    *,
    db: Any,
) -> CategoryResponse:
    """Update category."""
    async with db().begin() as transaction:
        db_category = await catalog_repository.update_category(
            category_id,
            category_data.model_dump(exclude_none=True),
            transaction=transaction,
        )
        await transaction.session.commit()
        return CategoryResponse.model_validate(db_category)


async def delete_category(
    category_id: int,
    *,
    db: Any,
) -> None:
    """Delete category."""
    async with db().begin() as transaction:
        await catalog_repository.delete_category(
            category_id,
            transaction=transaction,
        )
        await transaction.session.commit()


async def upload_category_image(
    category_id: int,
    *,
    db,
    image: UploadFile,
    image_client: Callable = file_upload,
) -> str:
    """Upload single image for category."""
    image_path = image_client.optimize_image(image)
    async with db().begin() as transaction:
        db_category = await catalog_repository.get_category_by_id(
            category_id,
            transaction=transaction,
        )
        if not db_category:
            raise CategoryNotFoundError
        db_category.image_path = image_path
        await transaction.session.commit()
    return db_category.image_path


async def upload_category_media_gallery(
    category_id: int,
    *,
    media_type: MediaType,
    media: UploadFile,
    order: int,
    db,
) -> str:
    """Upload media to category gallery."""
    media_path = None
    if media_type == MediaType.photo.value:
        media_path = file_upload.optimize_image(media)
    elif media_type == MediaType.video.value:
        media_path = await file_upload.upload_video(media)

    async with db().begin() as transaction:
        db_category = await catalog_repository.get_category_by_id(
            category_id,
            transaction=transaction,
        )
        if not db_category:
            raise CategoryNotFoundError

        db_media_upload = UploadedMediaDB(
            type=media_type,
            uri=media_path,
            order=order,
        )
        transaction.session.add(db_media_upload)
        await transaction.session.flush()
        logger.debug(f'Media id {db_media_upload.media_id}')

        db_media_gallery = CategoryMediaGalleryDB(
            media_id=db_media_upload.media_id,
            category_id=category_id,
        )
        transaction.session.add(db_media_gallery)
        await transaction.session.flush()
        gallery_id = db_media_gallery.category_media_gallery_id
        logger.debug(f'Category Media Gallery id {gallery_id}')
        logger.debug(f'Media id {db_media_gallery.media_id}')
        await transaction.session.commit()
    return media_path


async def delete_category_media_gallery(
    category_id: int,
    media_id: int,
    *,
    db,
) -> None:
    """Delete media from category gallery."""
    async with db().begin() as transaction:
        db_category = await catalog_repository.get_category_by_id(
            category_id,
            transaction=transaction,
        )
        if not db_category:
            raise CategoryNotFoundError

        query = select(CategoryMediaGalleryDB).where(
            CategoryMediaGalleryDB.category_id == category_id,
            CategoryMediaGalleryDB.media_id == media_id,
        )
        result = await transaction.session.execute(query)
        db_media_gallery = result.scalar_one_or_none()

        if not db_media_gallery:
            raise CategoryMediaNotFoundError

        # Delete the media gallery entry
        delete_stmt = delete(CategoryMediaGalleryDB).where(
            CategoryMediaGalleryDB.category_id == category_id,
            CategoryMediaGalleryDB.media_id == media_id,
        )
        await transaction.session.execute(delete_stmt)
        await transaction.session.commit()


async def get_category_media_gallery(
    category_id: int,
    *,
    db,
) -> list[UploadedMediaDB]:
    """Get all media from category gallery."""
    async with db().begin() as transaction:
        db_category = await catalog_repository.get_category_by_id(
            category_id,
            transaction=transaction,
        )
        if not db_category:
            raise CategoryNotFoundError

        query = (
            select(UploadedMediaDB)
            .join(CategoryMediaGalleryDB)
            .where(CategoryMediaGalleryDB.category_id == category_id)
            .order_by(UploadedMediaDB.order)
        )
        result = await transaction.session.execute(query)
        return list(result.scalars().all())
