from decimal import Decimal
import pytest
from app.entities.product import ProductCart

from models.order import Product


URL = '/cart/product'


@pytest.mark.asyncio
def test_add_product_in_new_cart(client, mocker, db) -> None:
    """Must add product in new cart and return cart."""
    # Arrange
    with db:
        product_db = Product(
            name='product 1',
            price=Decimal('100.00'),
            description='Test Product',
            direct_sales=None,
            installments_config=1,
            upsell=None,
            uri='/test_product',
            # installments_list={
            #     {'name': '1', 'value': 'R$100,00'},
            #     {'name': '2', 'value': 'R$50,00'},
            #     {'name': '3', 'value': 'R$33,00'},
            #     {'name': '4', 'value': 'R$25,00'},
            #     {'name': '5', 'value': 'R$20,00'},
            # },
        )
        db.add(product_db)

    # Act
    product = ProductCart(product_id=1, quantity=1)
    product.__delattr__('price')
    product.__delattr__('discount_price')
    response = client.post(URL, json=product.model_dump())

    # Assert
    assert response.status_code == 201
    assert response.json()
