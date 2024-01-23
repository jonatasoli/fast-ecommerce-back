from main import app
from httpx import AsyncClient
import pytest
from decimal import Decimal
from mail_service.sendmail import settings
from app.entities.cart import CartBase
from app.entities.product import ProductCart
from config import settings
from fastapi.encoders import jsonable_encoder
import redis

from tests.factories_db import (
    CategoryFactory,
    CreditCardFeeConfigFactory,
    InventoryDBFactory,
    ProductFactory,
)
from tests.fake_functions import fake, fake_url_path


URL = '/cart'


@pytest.mark.asyncio()
async def test_estimate_products_in_cart(db) -> None:
    """Must add product in new cart and return cart."""
    # Arrange
    with db:
        category = CategoryFactory()
        config_fee = CreditCardFeeConfigFactory()
        db.add_all([category, config_fee])
        db.flush()
        product_db_1 = ProductFactory(
            category=category,
            installment_config=config_fee,
            price=100,
        )
        product_db_2 = ProductFactory(
            category=category,
            installment_config=config_fee,
            price=200,
        )

        inventory_db_1 = InventoryDBFactory(
            product=product_db_1,
            product_id=1,
            inventory_id=1,
        )
        inventory_db_2 = InventoryDBFactory(
            product=product_db_2,
            product_id=2,
            inventory_id=2,
        )
        db.add_all([product_db_1, product_db_2])
        db.flush()
        db.add_all([inventory_db_1, inventory_db_2])
        db.commit()
    cart_items = []
    first_product = ProductCart(
        name=fake.name(),
        image_path=fake_url_path(),
        product_id=2,
        quantity=1,
        price=Decimal('100.00'),
    )
    second_product = ProductCart(
        name=fake.name(),
        image_path=fake_url_path(),
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
    pool = redis.ConnectionPool.from_url(
        url=settings.REDIS_URL,
        db=settings.REDIS_DB,
    )
    cache = redis.Redis(connection_pool=pool)
    cache.set(str(uuid), cart.model_dump_json())

    # Act
    async with AsyncClient(app=app, base_url='http://test') as client:
        response = await client.post(
            f'{URL}/{uuid!s}/estimate',
            json=jsonable_encoder(cart.model_dump()),
        )

    # Assert
    assert response.status_code == 201
    return_uuid = response.json()['uuid']
    return_cart_items = response.json()['cart_items']
    assert return_uuid == uuid
    assert len(return_cart_items) == 2
    assert response.json()['subtotal'] == str(cart.subtotal).split('.')[0]
