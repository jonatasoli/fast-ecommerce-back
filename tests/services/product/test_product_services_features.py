from io import BytesIO
import pytest
from fastapi import UploadFile
from faker import Faker
from sqlalchemy import select

from app.entities.product import ProductNotFoundError, ProductPatchRequest
from app.infra.constants import MediaType
from app.infra.models import MediaGalleryDB, UploadedMediaDB
from app.product.services import (
    product_not_found_exception,
    get_inventory,
    get_inventory_name,
    inventory_transaction,
    update_product,
    delete_product,
    upload_media_gallery,
    delete_media_gallery,
    get_media_gallery,
)
from tests.factories_db import (
    CategoryFactory,
    CreditCardFeeConfigFactory,
    ProductDBFactory,
)

fake = Faker()


@pytest.fixture
def real_upload_file():
    dummy_content = BytesIO(b'fake video content')
    return UploadFile(file=dummy_content, filename='test.mp4')


def test_product_not_found_exception_should_raise():
    with pytest.raises(ProductNotFoundError):
        product_not_found_exception()


@pytest.mark.asyncio
async def test_get_inventory_should_verify_admin_and_return_inventory(mocker, asyncdb):

    # Setup
    async def mock_verify_fn(token, db):
        return None

    mock_verify = mocker.patch(
        'app.product.services.verify_admin',
        side_effect=mock_verify_fn,
    )
    mock_repo = mocker.patch(
        'app.product.repository.get_inventory',
        return_value={'products': [], 'total': 0},
    )
    token = fake.uuid4()
    page = fake.random_int(min=1, max=10)
    offset = fake.random_int(min=10, max=50)

    # Act
    result = await get_inventory(
        token, page=page, offset=offset, db=asyncdb, verify_admin=mock_verify,
    )

    # Assert
    mock_verify.assert_called_once_with(token, db=asyncdb)
    mock_repo.assert_called_once()
    assert result == {'products': [], 'total': 0}


@pytest.mark.asyncio
async def test_get_inventory_name_should_return_inventory_by_name(mocker, asyncdb):
    # Setup
    mock_repo = mocker.patch(
        'app.product.repository.get_inventory',
        return_value={'products': [], 'total': 0},
    )
    path = fake.word()
    currency = 'BRL'
    page = fake.random_int(min=1, max=10)
    offset = fake.random_int(min=10, max=50)

    # Act
    result = await get_inventory_name(
        path, currency=currency, page=page, offset=offset, db=asyncdb,
    )

    # Assert
    mock_repo.assert_called_once()
    assert result == {'products': [], 'total': 0}


@pytest.mark.asyncio
async def test_inventory_transaction_should_add_transaction(mocker, asyncdb):
    # Setup
    mock_repo = mocker.patch(
        'app.product.repository.add_inventory_transaction',
        return_value=True,
    )
    product_id = fake.random_int()
    inventory = {'quantity': fake.random_int(min=1, max=100)}
    token = fake.uuid4()

    # Act
    result = await inventory_transaction(
        product_id, inventory=inventory, token=token, db=asyncdb,
    )

    # Assert
    mock_repo.assert_called_once()
    assert result is True


@pytest.mark.asyncio
async def test_update_product_should_update_fields(mocker, asyncdb):
    # Setup
    async with asyncdb().begin() as transaction:
        category = CategoryFactory()
        config_fee = CreditCardFeeConfigFactory()
        transaction.session.add_all([category, config_fee])
        await transaction.session.flush()

        product_db = ProductDBFactory(
            category=category,
            installment_config=config_fee,
            active=True,
            name='Old Name',
        )
        transaction.session.add(product_db)
        await transaction.session.commit()

    update_data = ProductPatchRequest(name='New Name', price=999.99)

    # Act
    await update_product(product_db.product_id, update_data=update_data, db=asyncdb)

    # Assert
    async with asyncdb().begin() as transaction:
        updated = await transaction.session.get(type(product_db), product_db.product_id)
        assert updated.name == 'New Name'


@pytest.mark.asyncio
async def test_update_product_not_found_should_raise(mocker, asyncdb):
    # Setup
    update_data = ProductPatchRequest(name='New Name')

    # Act / Assert
    with pytest.raises(ProductNotFoundError):
        await update_product(999, update_data=update_data, db=asyncdb)


@pytest.mark.asyncio
async def test_delete_product_should_delete(mocker, asyncdb):
    # Setup
    product_id = fake.random_int()

    # Mock the transaction and db context
    mock_transaction = mocker.MagicMock()
    mock_transaction.commit = mocker.MagicMock()
    mock_context = mocker.MagicMock()
    mock_context.__enter__ = mocker.MagicMock(return_value=mock_transaction)
    mock_context.__exit__ = mocker.MagicMock(return_value=None)
    mock_db_instance = mocker.MagicMock()
    mock_db_instance.begin = mocker.MagicMock(return_value=mock_context)

    mock_repo = mocker.patch(
        'app.product.repository.delete_product',
        return_value=None,
    )

    # Create a mock db callable
    mock_db = mocker.MagicMock(return_value=mock_db_instance)

    # Act
    await delete_product(product_id, db=mock_db)

    # Assert
    mock_repo.assert_called_once()


@pytest.mark.asyncio
async def test_upload_media_gallery_should_upload_video(
    real_upload_file, mocker, asyncdb,
):
    # Setup
    async with asyncdb().begin() as transaction:
        category = CategoryFactory()
        config_fee = CreditCardFeeConfigFactory()
        transaction.session.add_all([category, config_fee])
        await transaction.session.flush()

        product_db = ProductDBFactory(
            category=category,
            installment_config=config_fee,
            active=True,
        )
        transaction.session.add(product_db)
        await transaction.session.commit()

    mock_upload_video = mocker.patch(
        'app.infra.file_upload.upload_video',
        return_value='/media/video.mp4',
    )
    order = fake.random_int()
    media_type = MediaType.video

    # Act
    media_path = await upload_media_gallery(
        product_db.product_id,
        media_type=media_type,
        media=real_upload_file,
        order=order,
        db=asyncdb,
    )

    # Assert
    assert media_path == '/media/video.mp4'
    mock_upload_video.assert_called_once_with(real_upload_file)

    result = await asyncdb().execute(select(UploadedMediaDB))
    uploaded = result.scalar_one()
    assert uploaded.type == media_type
    assert uploaded.uri == '/media/video.mp4'


@pytest.mark.asyncio
async def test_delete_media_gallery_should_delete_media(mocker, asyncdb):
    # Setup
    async with asyncdb().begin() as transaction:
        category = CategoryFactory()
        config_fee = CreditCardFeeConfigFactory()
        transaction.session.add_all([category, config_fee])
        await transaction.session.flush()

        product_db = ProductDBFactory(
            category=category,
            installment_config=config_fee,
            active=True,
        )
        transaction.session.add(product_db)
        await transaction.session.flush()

        media = UploadedMediaDB(
            type=MediaType.photo,
            uri='/media/photo.png',
            order=1,
        )
        transaction.session.add(media)
        await transaction.session.flush()

        gallery = MediaGalleryDB(
            product_id=product_db.product_id,
            media_id=media.media_id,
        )
        transaction.session.add(gallery)
        await transaction.session.commit()

    # Act
    await delete_media_gallery(
        product_db.product_id, media_id=media.media_id, db=asyncdb,
    )

    # Assert
    result = await asyncdb().execute(select(MediaGalleryDB))
    assert result.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_get_media_gallery_should_return_media_list(mocker, asyncdb):
    # Setup
    async with asyncdb().begin() as transaction:
        category = CategoryFactory()
        config_fee = CreditCardFeeConfigFactory()
        transaction.session.add_all([category, config_fee])
        await transaction.session.flush()

        product_db = ProductDBFactory(
            category=category,
            installment_config=config_fee,
            active=True,
            uri=fake.slug(),
        )
        transaction.session.add(product_db)
        await transaction.session.flush()

        media1 = UploadedMediaDB(
            type=MediaType.photo,
            uri='/media/photo1.png',
            order=1,
        )
        media2 = UploadedMediaDB(
            type=MediaType.photo,
            uri='/media/photo2.png',
            order=2,
        )
        transaction.session.add_all([media1, media2])
        await transaction.session.flush()

        gallery1 = MediaGalleryDB(
            product_id=product_db.product_id,
            media_id=media1.media_id,
        )
        gallery2 = MediaGalleryDB(
            product_id=product_db.product_id,
            media_id=media2.media_id,
        )
        transaction.session.add_all([gallery1, gallery2])
        await transaction.session.commit()

    # Act
    result = await get_media_gallery(product_db.uri, db=asyncdb)

    # Assert
    assert len(result) == 2
    assert result[0].uri == '/media/photo1.png'
    assert result[1].uri == '/media/photo2.png'
