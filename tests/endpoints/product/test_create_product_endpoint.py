from decimal import ROUND_HALF_UP, Decimal
import random


from fastapi import status
from tests.factories_db import CategoryFactory, CreditCardFeeConfigFactory
from tests.fake_functions import fake, fake_url, fake_url_path

URL = '/product'


def test_given_valid_payload_should_create_product(t_client, db, admin_token):
    """Must create product by payload."""
    # Arrange
    category_id = None
    price = Decimal(
        random.random() * 100).quantize(Decimal('.01'),
        rounding=ROUND_HALF_UP,
    )
    with db:
        category = CategoryFactory()
        config_fee = CreditCardFeeConfigFactory()
        db.add_all([category, config_fee])
        db.commit()
        category_id = category.category_id
    product_data = {
        'name': fake.name(),
        'uri': fake_url(),
        'price': float(price),
        'category_id': category_id,
        'description': {'content': 'test', 'description': 'test'},
        'image_path': fake_url_path(),
        'sku': fake.pystr(),
    }
    headers = { 'Authorization': f'Bearer {admin_token}' }

    # Act
    response = t_client.post(URL, json=product_data, headers=headers)

    # Assert
    assert response.status_code == status.HTTP_201_CREATED
