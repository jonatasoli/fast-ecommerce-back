import httpx
import pytest
from decimal import Decimal
from mail_service.sendmail import settings
from app.entities.cart import CartBase
from app.entities.product import ProductCart
from config import settings
from app.infra.endpoints.cart import get_bootstrap
from app.infra.bootstrap import bootstrap
from fastapi.encoders import jsonable_encoder
import redis

from models.order import Product, Category
from tests.fake_functions import fake
from httpx import AsyncClient
from main import app


URL = '/cart/preview'


@pytest.mark.anyio
async def test_preview_product_cart(client, db) -> None:
    """Must add product in new cart and return cart."""
    # Arrange
    with db:
        category = Category(
            name='category1',
            path='/test',
        )
        product_db_1 = Product(
            name='product 1',
            price=Decimal('100.00'),
            description='Test Product',
            direct_sales=None,
            installments_config=1,
            upsell=None,
            uri='/test_product_1',
            category_id=1,
            sku='code1',
        )
        product_db_2 = Product(
            name='product 2',
            price=Decimal('200.00'),
            description='Test Product',
            direct_sales=None,
            installments_config=1,
            upsell=None,
            uri='/test_product_2',
            category_id=1,
            sku='code2',
        )
        db.add(category)
        db.add_all([product_db_1, product_db_2])
        db.commit()
    cart_items = []
    first_product = ProductCart(
        product_id=2,
        quantity=1,
        price=Decimal('100.00'),
    )
    second_product = ProductCart(
        product_id=1,
        quantity=1,
        price=Decimal('200.00'),
    )
    cart_items.append(first_product)
    cart_items.append(second_product)
    uuid = fake.uuid4()
    cart = CartBase(
        uuid=uuid,
        cart_items=cart_items,
        subtotal=Decimal('300.00'),
    )
    pool = redis.ConnectionPool(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB,
    )
    cache = redis.Redis(connection_pool=pool)
    cache.set(str(uuid), cart.model_dump_json())

    response = await client.post(
        f'{URL}/{str(uuid)}', json=jsonable_encoder(cart.model_dump())
    )

    # Assert
    assert response.status_code == 201
    return_uuid = response.json()['uuid']
    return_cart_items = response.json()['cart_items']
    assert return_uuid == uuid
    assert len(return_cart_items) == 2
    assert response.json()['subtotal'] == str(cart.subtotal).split('.')[0]
