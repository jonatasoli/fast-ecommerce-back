import random


from fastapi import status
from tests.factories_db import CategoryFactory, CreditCardFeeConfigFactory
from tests.fake_functions import fake, fake_url, fake_url_path

URL = '/product/create-product'


def test_given_valid_payload_should_create_product(t_client, db):
    """Must create product by payload."""
    # Arrange
    category_id = None
    price = random.random() * 100
    with db:
        category = CategoryFactory()
        config_fee = CreditCardFeeConfigFactory()
        db.add_all([category, config_fee])
        db.commit()
        category_id = category.category_id
    product_data = {
        'name': fake.name(),
        'uri': fake_url(),
        'price': price,
        'category_id': category_id,
        'description': {'content': 'test', 'description': 'test'},
        'image_path': fake_url_path(),
        'sku': fake.pystr(),
    }

    # Act
    response = t_client.post(URL, json=product_data)

    # Assert
    assert response.status_code == status.HTTP_201_CREATED
