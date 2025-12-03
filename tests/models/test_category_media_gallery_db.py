from sqlalchemy import select
from app.infra.models import CategoryMediaGalleryDB, CategoryDB, UploadedMediaDB
from tests.factories_db import CategoryFactory, UploadedMediaFactory


def test_create_category_media_gallery(session):
    """Must create valid category media gallery."""
    # Arrange
    category = CategoryFactory()
    media = UploadedMediaFactory()
    session.add_all([category, media])
    session.commit()

    new_gallery = CategoryMediaGalleryDB(
        category_id=category.category_id,
        media_id=media.media_id,
    )
    session.add(new_gallery)
    session.commit()

    # Act
    gallery = session.scalar(
        select(CategoryMediaGalleryDB).where(
            CategoryMediaGalleryDB.category_media_gallery_id == new_gallery.category_media_gallery_id,
        ),
    )

    # Assert
    assert gallery.category_media_gallery_id is not None
    assert gallery.category_id == category.category_id
    assert gallery.media_id == media.media_id


def test_category_media_gallery_foreign_keys(session):
    """Must enforce foreign key constraints."""
    # Arrange
    category = CategoryFactory()
    media = UploadedMediaFactory()
    session.add_all([category, media])
    session.commit()

    gallery = CategoryMediaGalleryDB(
        category_id=category.category_id,
        media_id=media.media_id,
    )
    session.add(gallery)
    session.commit()

    # Act - Query related objects
    result_gallery = session.scalar(
        select(CategoryMediaGalleryDB).where(
            CategoryMediaGalleryDB.category_id == category.category_id,
        ),
    )
    result_category = session.scalar(
        select(CategoryDB).where(CategoryDB.category_id == category.category_id),
    )
    result_media = session.scalar(
        select(UploadedMediaDB).where(UploadedMediaDB.media_id == media.media_id),
    )

    # Assert
    assert result_gallery is not None
    assert result_category is not None
    assert result_media is not None
    assert result_gallery.category_id == result_category.category_id
    assert result_gallery.media_id == result_media.media_id
