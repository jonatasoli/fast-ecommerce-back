import pytest
from app.entities.product import ProductCreate, ProductInDBResponse

from app.product.services import create_product
from tests.factories_db import CategoryFactory, CreditCardFeeConfigFactory
from tests.fake_functions import fake, fake_decimal, fake_url, fake_url_path


@pytest.mark.asyncio
async def test_give_valid_product_payload_should_create_product(
    asyncdb,
) -> None:
    category = CategoryFactory()
    config_fee = CreditCardFeeConfigFactory()
    async with asyncdb() as db:
        db.add_all([category, config_fee])
        await db.commit()
    description = {'content': 'test', 'description': 'test'}

    product_data = ProductCreate(
        name=fake.name(),
        uri=fake_url(),
        price=fake_decimal(),
        description=description,
        image_path=fake_url_path(),
        category_id=category.category_id,
        sku=fake.pystr(),
    )

    # Act
    product_response = await create_product(product_data, db=asyncdb)

    # Assert
    assert product_response
    assert isinstance(product_response, ProductInDBResponse)
    assert product_response.product_id is not None
