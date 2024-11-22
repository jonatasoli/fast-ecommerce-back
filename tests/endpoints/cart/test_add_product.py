from decimal import Decimal

from httpx import AsyncClient
from app.infra.database import get_async_session
from main import app
import pytest
import redis
from app.entities.cart import CartBase
from app.entities.product import ProductCart
from tests.factories_db import (
    CategoryFactory,
    CreditCardFeeConfigFactory,
    ProductDBFactory,
)
from tests.fake_functions import fake, fake_url_path
from config import settings


URL = '/cart'


@pytest.mark.asyncio
async def test_add_product_in_new_cart(asyncdb) -> None:
    """Must add product in new cart and return cart."""
    # Arrange
    async with asyncdb().begin() as transaction:
        category = CategoryFactory()
        config_fee = CreditCardFeeConfigFactory()
        transaction.session.add_all([category, config_fee])
        await transaction.session.flush()
        product_db = ProductDBFactory(
            category=category,
            installment_config=config_fee,
            price=10000,
        )
        transaction.session.add(product_db)
        await transaction.session.commit()
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
    product = ProductCart(
        name=fake.name(),
        image_path=fake_url_path(),
        product_id=1,
        quantity=1,
    )
    product.__delattr__('discount_price')
    async with AsyncClient(app=app, base_url='http://test') as client:
        app.dependency_overrides[get_async_session] = lambda: asyncdb
        response = await client.post(
            f'{URL}/{uuid}/product',
            json=product.model_dump(),
        )

    # Assert
    assert response.status_code == 201
    assert response.json()
