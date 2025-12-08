# ruff: noqa: I001
import pytest
import json
from decimal import Decimal
from app.entities.product import ProductInDBResponse
from tests.fake_functions import fake, fake_url, fake_url_path

URL = '/product/'


@pytest.mark.asyncio
async def test_given_valid_payload_should_create_product(
    async_client, mocker, async_admin_token,
):
    # Setup
    product_id = 1
    price = Decimal('99.99')
    description_dict = {'content': 'test', 'description': 'test'}

    mock_product = ProductInDBResponse(
        product_id=product_id,
        name=fake.name(),
        uri=fake_url(),
        price=price,
        category_id=1,
        description=json.dumps(description_dict),
        image_path=fake_url_path(),
        showcase=False,
    )

    mocker.patch('app.product.services.create_product', return_value=mock_product)
    mocker.patch('app.user.services.verify_admin', return_value=True)

    product_data = {
        'name': mock_product.name,
        'uri': mock_product.uri,
        'price': float(price),
        'category_id': mock_product.category_id,
        'description': description_dict,
        'image_path': mock_product.image_path,
        'sku': fake.pystr(),
    }
    headers = {'Authorization': f'Bearer {async_admin_token}'}

    # Act
    response = await async_client.post(
        URL,
        json=product_data,
        headers=headers,
    )

    # Assert
    assert response.status_code == 201
    assert response.json()['product_id'] == product_id
