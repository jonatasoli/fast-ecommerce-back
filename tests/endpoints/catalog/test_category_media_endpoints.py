from io import BytesIO
from fastapi import status
from app.infra.database import get_async_session
from main import app
from httpx import ASGITransport, AsyncClient
import pytest

from tests.factories_db import CategoryFactory, CreditCardFeeConfigFactory


URL_UPLOAD_IMAGE = '/catalog/category/upload-image'
URL_MEDIA = '/catalog/category/media'


@pytest.mark.asyncio
async def test_upload_category_image_should_return_200(asyncdb, admin_token, mocker):
    """Should upload image for category."""
    # Arrange
    async with asyncdb().begin() as transaction:
        category = CategoryFactory()
        config_fee = CreditCardFeeConfigFactory()
        transaction.session.add_all([category, config_fee])
        await transaction.session.commit()

    mocker.patch(
        'app.infra.file_upload.optimize_image',
        return_value='https://cdn.test.com/category.png',
    )

    dummy_image = BytesIO(b'fake image content')

    # Act
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url='http://test',
    ) as client:
        app.dependency_overrides[get_async_session] = lambda: asyncdb
        response = await client.post(
            f'{URL_UPLOAD_IMAGE}/{category.category_id}',
            files={'image': ('test.png', dummy_image, 'image/png')},
            headers={'Authorization': f'Bearer {admin_token}'},
        )

    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert 'https://cdn.test.com/category.png' in response.json()


@pytest.mark.asyncio
async def test_upload_category_image_not_found_should_return_404(asyncdb, admin_token, mocker):
    """Should return 404 when category not found."""
    # Arrange
    async with asyncdb().begin() as transaction:
        config_fee = CreditCardFeeConfigFactory()
        transaction.session.add(config_fee)
        await transaction.session.commit()

    mocker.patch(
        'app.infra.file_upload.optimize_image',
        return_value='https://cdn.test.com/category.png',
    )

    dummy_image = BytesIO(b'fake image content')

    # Act
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url='http://test',
    ) as client:
        app.dependency_overrides[get_async_session] = lambda: asyncdb
        response = await client.post(
            f'{URL_UPLOAD_IMAGE}/999',
            files={'image': ('test.png', dummy_image, 'image/png')},
            headers={'Authorization': f'Bearer {admin_token}'},
        )

    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_upload_category_media_gallery_should_return_201(asyncdb, admin_token, mocker):
    """Should upload media to category gallery."""
    # Arrange
    async with asyncdb().begin() as transaction:
        category = CategoryFactory()
        config_fee = CreditCardFeeConfigFactory()
        transaction.session.add_all([category, config_fee])
        await transaction.session.commit()

    mocker.patch(
        'app.infra.file_upload.optimize_image',
        return_value='https://cdn.test.com/gallery.png',
    )

    dummy_image = BytesIO(b'fake image content')

    # Act
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url='http://test',
    ) as client:
        app.dependency_overrides[get_async_session] = lambda: asyncdb
        response = await client.post(
            f'{URL_MEDIA}/{category.category_id}?media_type=PHOTO&order=1',
            files={'new_media': ('test.png', dummy_image, 'image/png')},
            headers={'Authorization': f'Bearer {admin_token}'},
        )

    # Assert
    assert response.status_code == status.HTTP_201_CREATED
    assert 'https://cdn.test.com/gallery.png' in response.json()


@pytest.mark.asyncio
async def test_get_category_media_gallery_should_return_200(asyncdb, admin_token, mocker):
    """Should get media gallery for category."""
    # Arrange
    async with asyncdb().begin() as transaction:
        category = CategoryFactory()
        config_fee = CreditCardFeeConfigFactory()
        transaction.session.add_all([category, config_fee])
        await transaction.session.commit()

    # Act
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url='http://test',
    ) as client:
        app.dependency_overrides[get_async_session] = lambda: asyncdb
        response = await client.get(
            f'{URL_MEDIA}/{category.category_id}',
        )

    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_delete_category_media_should_return_204(asyncdb, admin_token, mocker):
    """Should delete media from category gallery."""
    # Arrange
    from app.infra.models import UploadedMediaDB, CategoryMediaGalleryDB

    async with asyncdb().begin() as transaction:
        category = CategoryFactory()
        config_fee = CreditCardFeeConfigFactory()
        transaction.session.add_all([category, config_fee])
        await transaction.session.flush()

        media = UploadedMediaDB(
            type='PHOTO',
            uri='https://cdn.test.com/test.png',
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
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url='http://test',
    ) as client:
        app.dependency_overrides[get_async_session] = lambda: asyncdb
        response = await client.delete(
            f'{URL_MEDIA}/{category.category_id}?media_id={media.media_id}',
            headers={'Authorization': f'Bearer {admin_token}'},
        )

    # Assert
    assert response.status_code == status.HTTP_204_NO_CONTENT
