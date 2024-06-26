from pytest_mock import MockerFixture
from app.product import repository
from app.product.services import upload_image
from tests.factories_db import ProductDBFactory
from tests.fake_functions import fake_file
import pytest


@pytest.mark.asyncio()
async def test_upload_image_should_change_image_path(
    mocker: MockerFixture,
    asyncdb,
) -> None:
    """Should change image patch in specifict product_id."""
    # Arrange
    product_db = ProductDBFactory()
    product_id = product_db.product_id
    new_image_path = 'https://cdn.site.com/new_image_path'
    mocker.patch.object(
        repository,
        'get_product_by_id',
        return_value=product_db,
    )
    image_client_mock = mocker.Mock()
    image_client_mock.optimize_image.return_value = new_image_path

    # Act
    session = await asyncdb
    response = await upload_image(
        product_id,
        db=session,
        image=fake_file(),
        image_client=image_client_mock,
    )

    # Arrange
    assert response == new_image_path
