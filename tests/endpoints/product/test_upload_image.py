from httpx import AsyncClient
from main import app
import pytest
from tests.factories_db import (
    CategoryFactory,
    CreditCardFeeConfigFactory,
    ProductDBFactory,
)


URL = '/product'


@pytest.mark.skip('TODO: need create mock file upload')
async def test_add_new_image_file_in_product(
    asyncdb,
) -> None:
    """Must add product in new cart and return cart."""
    # Arrange
    product_id = None
    db = await asyncdb()
    async with db().begin() as transaction:
        category = CategoryFactory()
        config_fee = CreditCardFeeConfigFactory()
        transaction.add_all([category, config_fee])
        await transaction.flush()
        product_db = ProductDBFactory(
            category=category,
            installment_config=config_fee,
        )
        transaction.add(product_db)
        await transaction.commit()
        product_id = product_db.product_id

    # Act
    async with AsyncClient(app=app, base_url='http://test') as client:
        response = await client.post(
            f'{URL}/upload-image/{product_id}',
            headers={'Content-Type': 'multipart/form-data'},
        )

    # Assert
    assert response.status_code == 200
    assert response.json()
