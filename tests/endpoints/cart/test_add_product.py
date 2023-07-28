from decimal import Decimal
from httpx import AsyncClient
import pytest
from app.entities.product import ProductCart
from main import app
from httpx import AsyncClient

from models.order import Category, Product


URL = '/cart/product'


@pytest.mark.anyio
async def test_add_product_in_new_cart(client, db) -> None:
    """Must add product in new cart and return cart."""
    # Arrange
    with db:
        category = Category(
            name='category1',
            path='/test',
        )
        product_db = Product(
            name='product 1',
            price=Decimal('100.00'),
            description='Test Product',
            direct_sales=None,
            category_id=1,
            installments_config=1,
            upsell=None,
            uri='/test_product',
            sku='code1',
        )
        db.add(category)
        db.add(product_db)
        db.commit()

    # Act
    product = ProductCart(product_id=1, quantity=1)
    product.__delattr__('discount_price')
    response = await client.post(URL, json=product.model_dump())

    # Assert
    assert response.status_code == 201
    assert response.json()
