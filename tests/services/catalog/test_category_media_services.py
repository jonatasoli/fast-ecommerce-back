# ruff: noqa: I001
from io import BytesIO
import pytest
from fastapi import UploadFile, HTTPException
from pytest_mock import MockerFixture
from sqlalchemy import select

from app.catalog.services import (
    upload_category_image,
    upload_category_media_gallery,
    delete_category_media_gallery,
    get_category_media_gallery,
)
from app.infra.constants import MediaType
from app.entities.category import CategoryMediaNotFoundError, CategoryNotFoundError
from app.infra.models import CategoryMediaGalleryDB, UploadedMediaDB
from tests.factories_db import CategoryFactory, CreditCardFeeConfigFactory
from tests.fake_functions import fake_file


@pytest.mark.asyncio
async def test_upload_category_image_should_update_image_path(
    mocker: MockerFixture,
    asyncdb,
):
    # Setup
    async with asyncdb().begin() as transaction:
        category = CategoryFactory()
        config_fee = CreditCardFeeConfigFactory()
        transaction.session.add_all([category, config_fee])
        await transaction.session.commit()

    new_image_path = 'https://cdn.test.com/category.png'
    image_client_mock = mocker.Mock()
    image_client_mock.optimize_image.return_value = new_image_path

    # Act
    result = await upload_category_image(
        category.category_id,
        db=asyncdb,
        image=fake_file(),
        image_client=image_client_mock,
    )

    # Assert
    assert result == new_image_path
    image_client_mock.optimize_image.assert_called_once()


@pytest.mark.asyncio
async def test_upload_category_image_not_found_should_raise_exception(
    mocker: MockerFixture,
    asyncdb,
):
    # Setup
    from app.entities.category import CategoryNotFoundError

    async with asyncdb().begin() as transaction:
        config_fee = CreditCardFeeConfigFactory()
        transaction.session.add(config_fee)
        await transaction.session.commit()

    image_client_mock = mocker.Mock()
    image_client_mock.optimize_image.return_value = 'https://cdn.test.com/category.png'

    # Act & Assert
    with pytest.raises(CategoryNotFoundError):
        await upload_category_image(
            999,
            db=asyncdb,
            image=fake_file(),
            image_client=image_client_mock,
        )


@pytest.fixture
def real_upload_file():
    dummy_content = BytesIO(b'fake image content')
    return UploadFile(file=dummy_content, filename='test.png')


@pytest.fixture
def mock_optimize_image(mocker):
    return mocker.patch(
        'app.infra.file_upload.optimize_image',
        return_value='/media/category-image.png',
    )


@pytest.mark.asyncio
async def test_upload_category_media_gallery_should_upload_photo(
    real_upload_file,
    mock_optimize_image,
    asyncdb,
):
    # Setup
    async with asyncdb().begin() as transaction:
        category = CategoryFactory()
        config_fee = CreditCardFeeConfigFactory()
        transaction.session.add_all([category, config_fee])
        await transaction.session.commit()

    order = 1
    media_type = MediaType.photo

    # Act
    media_path = await upload_category_media_gallery(
        category.category_id,
        media_type=media_type,
        media=real_upload_file,
        order=order,
        db=asyncdb,
    )

    # Assert
    assert media_path == '/media/category-image.png'
    mock_optimize_image.assert_called_once_with(real_upload_file)

    result = await asyncdb().execute(select(UploadedMediaDB))
    uploaded = result.scalar_one()
    assert uploaded.type == media_type
    assert uploaded.uri == '/media/category-image.png'
    assert uploaded.order == order

    result = await asyncdb().execute(select(CategoryMediaGalleryDB))
    gallery = result.scalar_one()
    assert gallery.category_id == category.category_id
    assert gallery.media_id == uploaded.media_id


@pytest.mark.asyncio
async def test_upload_category_media_gallery_should_upload_video(
    real_upload_file,
    mocker,
    asyncdb,
):
    # Setup
    async with asyncdb().begin() as transaction:
        category = CategoryFactory()
        config_fee = CreditCardFeeConfigFactory()
        transaction.session.add_all([category, config_fee])
        await transaction.session.commit()

    order = 1
    media_type = MediaType.video
    mock_upload_video = mocker.patch(
        'app.infra.file_upload.upload_video',
        return_value='/media/category-video.mp4',
    )

    # Act
    media_path = await upload_category_media_gallery(
        category.category_id,
        media_type=media_type,
        media=real_upload_file,
        order=order,
        db=asyncdb,
    )

    # Assert
    assert media_path == '/media/category-video.mp4'
    mock_upload_video.assert_called_once_with(real_upload_file)

    result = await asyncdb().execute(select(UploadedMediaDB))
    uploaded = result.scalar_one()
    assert uploaded.type == media_type
    assert uploaded.uri == '/media/category-video.mp4'
    assert uploaded.order == order

    result = await asyncdb().execute(select(CategoryMediaGalleryDB))
    gallery = result.scalar_one()
    assert gallery.category_id == category.category_id
    assert gallery.media_id == uploaded.media_id


@pytest.mark.asyncio
async def test_upload_category_media_gallery_category_not_found_should_raise(
    real_upload_file,
    mock_optimize_image,
    asyncdb,
):
    # Setup
    from app.entities.category import CategoryNotFoundError

    async with asyncdb().begin() as transaction:
        config_fee = CreditCardFeeConfigFactory()
        transaction.session.add(config_fee)
        await transaction.session.commit()

    # Act & Assert
    with pytest.raises(CategoryNotFoundError):
        await upload_category_media_gallery(
            999,
            media_type=MediaType.photo,
            media=real_upload_file,
            order=1,
            db=asyncdb,
        )


@pytest.mark.asyncio
async def test_get_category_media_gallery_should_return_media_list(asyncdb):
    # Setup
    async with asyncdb().begin() as transaction:
        category = CategoryFactory()
        config_fee = CreditCardFeeConfigFactory()
        transaction.session.add_all([category, config_fee])
        await transaction.session.flush()

        media1 = UploadedMediaDB(
            type='PHOTO',
            uri='https://cdn.test.com/photo1.png',
            order=1,
        )
        media2 = UploadedMediaDB(
            type='PHOTO',
            uri='https://cdn.test.com/photo2.png',
            order=2,
        )
        transaction.session.add_all([media1, media2])
        await transaction.session.flush()

        # Link media to category
        gallery1 = CategoryMediaGalleryDB(
            category_id=category.category_id,
            media_id=media1.media_id,
        )
        gallery2 = CategoryMediaGalleryDB(
            category_id=category.category_id,
            media_id=media2.media_id,
        )
        transaction.session.add_all([gallery1, gallery2])
        await transaction.session.commit()

    # Act
    result = await get_category_media_gallery(category.category_id, db=asyncdb)

    # Assert
    assert len(result) == 2
    assert result[0].uri == 'https://cdn.test.com/photo1.png'
    assert result[1].uri == 'https://cdn.test.com/photo2.png'


@pytest.mark.asyncio
async def test_get_category_media_gallery_category_not_found_should_raise(asyncdb):
    # Setup
    from app.entities.category import CategoryNotFoundError

    async with asyncdb().begin() as transaction:
        config_fee = CreditCardFeeConfigFactory()
        transaction.session.add(config_fee)
        await transaction.session.commit()

    # Act & Assert
    with pytest.raises(CategoryNotFoundError):
        await get_category_media_gallery(999, db=asyncdb)


@pytest.mark.asyncio
async def test_delete_category_media_gallery_should_delete_media(asyncdb):
    # Setup
    async with asyncdb().begin() as transaction:
        category = CategoryFactory()
        config_fee = CreditCardFeeConfigFactory()
        transaction.session.add_all([category, config_fee])
        await transaction.session.flush()

        media = UploadedMediaDB(
            type='PHOTO',
            uri='https://cdn.test.com/photo.png',
            order=1,
        )
        transaction.session.add(media)
        await transaction.session.flush()

        gallery = CategoryMediaGalleryDB(
            category_id=category.category_id,
            media_id=media.media_id,
        )
        transaction.session.add(gallery)
        await transaction.session.commit()

    # Act
    await delete_category_media_gallery(
        category.category_id,
        media.media_id,
        db=asyncdb,
    )

    # Assert - Gallery entry should be deleted
    result = await asyncdb().execute(select(CategoryMediaGalleryDB))
    assert result.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_delete_category_media_gallery_category_not_found_should_raise(asyncdb):
    # Setup
    from app.entities.category import CategoryNotFoundError

    async with asyncdb().begin() as transaction:
        config_fee = CreditCardFeeConfigFactory()
        transaction.session.add(config_fee)
        await transaction.session.commit()

    # Act & Assert
    with pytest.raises(CategoryNotFoundError):
        await delete_category_media_gallery(999, 1, db=asyncdb)


@pytest.mark.asyncio
async def test_delete_category_media_gallery_media_not_found_should_raise(asyncdb):
    # Setup
    from app.entities.category import CategoryMediaNotFoundError

    async with asyncdb().begin() as transaction:
        category = CategoryFactory()
        config_fee = CreditCardFeeConfigFactory()
        transaction.session.add_all([category, config_fee])
        await transaction.session.commit()

    # Act & Assert
    with pytest.raises(CategoryMediaNotFoundError):
        await delete_category_media_gallery(
            category.category_id,
            999,
            db=asyncdb,
        )
