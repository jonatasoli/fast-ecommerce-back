from app.infra.database import get_async_session
from main import app
from httpx import AsyncClient
import pytest
from decimal import Decimal
from mail_service.sendmail import settings
from app.entities.cart import CartBase
from app.entities.product import ProductCart
from fastapi.encoders import jsonable_encoder
import redis

from tests.factories_db import (
    CategoryFactory,
    CreditCardFeeConfigFactory,
    InventoryDBFactory,
    ProductDBFactory,
)
from tests.fake_functions import fake, fake_url_path


URL = '/cart'


@pytest.mark.asyncio
async def test_estimate_products_in_cart(asyncdb) -> None:
    """Must add product in new cart and return cart."""
    # Arrange
    async with asyncdb().begin() as transaction:
        category = CategoryFactory()
        config_fee = CreditCardFeeConfigFactory()
        transaction.session.add_all([category, config_fee])
        await transaction.session.flush()
        product_db_1 = ProductDBFactory(
            category=category,
            installment_config=config_fee,
            price=100,
        )
        product_db_2 = ProductDBFactory(
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
        transaction.session.add_all([product_db_1, product_db_2])
        await transaction.session.flush()
        transaction.session.add_all([inventory_db_1, inventory_db_2])
        await transaction.session.commit()
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
    post_url = f'{URL}/{uuid!s}/estimate'
    async with AsyncClient(app=app, base_url='http://test') as client:
        app.dependency_overrides[get_async_session] = lambda: asyncdb
        response = await client.post(
            post_url,
            json=jsonable_encoder(cart.model_dump()),
        )

    # Assert
    assert response.status_code == 201
    return_uuid = response.json()['uuid']
    return_cart_items = response.json()['cart_items']
    assert return_uuid == uuid
    assert len(return_cart_items) == 2
    assert (
        response.json()['subtotal'].split('.')[0]
        == str(cart.subtotal).split('.')[0]
    )
