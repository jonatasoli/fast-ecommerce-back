from decimal import Decimal
import pytest
import redis
from app.entities.cart import CartBase
from app.entities.product import ProductCart
from tests.factories_db import (
    CategoryFactory,
    CreditCardFeeConfigFactory,
    ProductFactory,
)
from tests.fake_functions import fake
from config import settings


URL = '/cart'


@pytest.mark.anyio()
async def test_add_product_in_new_cart(client, db) -> None:
    """Must add product in new cart and return cart."""
    # Arrange
    with db:
        category = CategoryFactory()
        config_fee = CreditCardFeeConfigFactory()
        db.add_all([category, config_fee])
        db.flush()
        product_db = ProductFactory(
            category=category,
            installment_config=config_fee,
            price=10000,
        )
        db.add(category)
        db.add(product_db)
        db.commit()
    uuid = fake.uuid4()
    cart = CartBase(
        uuid=uuid,
        cart_items=[],
        subtotal=Decimal('0.00'),
    )
    pool = redis.ConnectionPool.from_url(
        url=settings.REDIS_URL,
        db=settings.REDIS_DB,
    )
    cache = redis.Redis(connection_pool=pool)
    cache.set(str(uuid), cart.model_dump_json())

    # Act
    product = ProductCart(product_id=1, quantity=1)
    product.__delattr__('discount_price')
    response = await client.post(
        f'{URL}/{uuid}/product',
        json=product.model_dump(),
    )

    # Assert
    assert response.status_code == 201
    assert response.json()
