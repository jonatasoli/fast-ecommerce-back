# ruff: noqa: I001
from io import BytesIO
from faker_file.providers.png_file import GraphicPngFileProvider
from fastapi import UploadFile
import pytest
from faker import Faker
from sqlalchemy import select, exc

from app.infra.constants import MediaType
from app.infra.file_upload import FileUploadBucketError
from app.infra.models import MediaGalleryDB, UploadedMediaDB
from app.product.services import upload_media_gallery
from tests.factories_db import (
    CategoryFactory,
    CreditCardFeeConfigFactory,
    ProductDBFactory,
)

fake = Faker()
fake.add_provider(GraphicPngFileProvider)


@pytest.fixture
def real_upload_file():
    dummy_content = BytesIO(b'fake image content')
    return UploadFile(file=dummy_content, filename='test.png')


@pytest.fixture
def mock_optimize_image(mocker):
    return mocker.patch(
        'app.infra.file_upload.optimize_image',
        return_value='/media/image.png',
    )


@pytest.mark.asyncio
async def test_image_in_gallery_must_upload(
    real_upload_file, mock_optimize_image, asyncdb,
):
    # Setup
    category = CategoryFactory()
    config_fee = CreditCardFeeConfigFactory()
    async with asyncdb().begin() as transaction:
        transaction.session.add_all([category, config_fee])
        await transaction.session.flush()
        product_db = ProductDBFactory(
            category=category,
            installment_config=config_fee,
            active=True,
        )
        transaction.session.add(product_db)
        await transaction.session.commit()
    order = fake.random_int()
    media_type = MediaType.photo

    # Act
    image_path = await upload_media_gallery(
        product_db.product_id,
        media_type=media_type,
        media=real_upload_file,
        order=order,
        db=asyncdb,
    )

    # Assert
    assert image_path == '/media/image.png'
    mock_optimize_image.assert_called_once_with(real_upload_file)

    # Verify UploadedMediaDB persisted
    result = await asyncdb().execute(select(UploadedMediaDB))
    uploaded = result.scalar_one()
    assert uploaded.type == media_type
    assert uploaded.uri == '/media/image.png'
    assert uploaded.order == order

    # Verify MediaGalleryDB persisted
    result = await asyncdb().execute(select(MediaGalleryDB))
    gallery = result.scalar_one()
    assert gallery.product_id == product_db.product_id
    assert gallery.media_id == uploaded.media_id


@pytest.mark.asyncio
async def test_media_with_invalid_product_should_raise_exception(
    asyncdb,
    real_upload_file,
    mock_optimize_image,
):
    # Setup
    category = CategoryFactory()
    config_fee = CreditCardFeeConfigFactory()
    async with asyncdb().begin() as transaction:
        transaction.session.add_all([category, config_fee])
        await transaction.session.commit()
    order = fake.random_int()
    media_type = MediaType.photo

    # Act
    with pytest.raises(Exception) as exc:
        await upload_media_gallery(
            1,
            media_type=media_type,
            media=real_upload_file,
            order=order,
            db=asyncdb,
        )

    assert exc


async def test_media_with_invalid_media_should_raise_exception(
    asyncdb,
    real_upload_file,
):
    # Setup
    category = CategoryFactory()
    config_fee = CreditCardFeeConfigFactory()
    async with asyncdb().begin() as transaction:
        transaction.session.add_all([category, config_fee])
        await transaction.session.flush()
        product_db = ProductDBFactory(
            category=category,
            installment_config=config_fee,
            active=True,
        )
        await transaction.session.commit()
    order = fake.random_int()
    media_type = MediaType.photo

    # Act
    with pytest.raises(FileUploadBucketError) as exc:
        await upload_media_gallery(
            product_db.product_id,
            media_type=media_type,
            media=real_upload_file,
            order=order,
            db=asyncdb,
        )

    assert exc
