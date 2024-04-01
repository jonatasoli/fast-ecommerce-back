from app.entities.product import ProductCreate, ProductInDBResponse

from app.order.services import create_product
from tests.factories_db import CategoryFactory, CreditCardFeeConfigFactory
from tests.fake_functions import fake, fake_decimal, fake_url, fake_url_path


def test_give_valid_product_payload_should_create_product(
    db,
) -> None:
    """Must create valid product."""
    category = CategoryFactory()
    config_fee = CreditCardFeeConfigFactory()
    db.add_all([category, config_fee])
    db.commit()
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
    product_response = create_product(product_data, db=db)

    # Assert
    assert product_response
    assert isinstance(product_response, ProductInDBResponse)
    assert product_response.product_id == 1
