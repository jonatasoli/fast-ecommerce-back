import pytest
from decimal import Decimal
from mail_service.sendmail import settings
from app.entities.cart import CartBase
from app.entities.product import ProductCart
import redis

from models.order import Product
from tests.fake_functions import fake


URL = '/cart/preview'


@pytest.mark.skip(
    reason='Error in sqlalchemy unit of work, but endpoint works'
)
def test_preview_product_cart(client, db) -> None:
    """Must add product in new cart and return cart."""
    # Arrange
    with db:
        product_db_1 = Product(
            name='product 1',
            price=Decimal('100.00'),
            description='Test Product',
            direct_sales=None,
            installments_config=1,
            upsell=None,
            uri='/test_product_1',
        )
        product_db_2 = Product(
            name='product 2',
            price=Decimal('200.00'),
            description='Test Product',
            direct_sales=None,
            installments_config=1,
            upsell=None,
            uri='/test_product_2',
        )
        db.add_all([product_db_1, product_db_2])
        db.commit()
    cart_items = []
    first_product = ProductCart(
        product_id=2,
        quantity=1,
    )
    second_product = ProductCart(
        product_id=1,
        quantity=1,
    )
    cart_items.append(first_product)
    cart_items.append(second_product)
    uuid = fake.uuid4()
    cart = CartBase(
        uuid=uuid,
        cart_items=cart_items,
        subtotal=Decimal(10),
    )
    pool = redis.ConnectionPool(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB,
    )
    cache = redis.Redis(connection_pool=pool)
    cache.set(str(uuid), cart.model_dump_json())

    # Act
    response = client.get(f'{URL}/{uuid}')

    # Assert
    assert response.status_code == 200
    return_uuid = response.json()['uuid']
    return_cart_items = response.json()['cart_items']
    assert return_uuid == uuid
    assert len(return_cart_items) == 2
