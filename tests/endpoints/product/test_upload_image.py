from decimal import Decimal
from io import BytesIO

from httpx import AsyncClient
from pytest_mock import MockerFixture
from sqlalchemy.orm import Session
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
from tests.fake_functions import fake, fake_file, fake_url_path
from config import settings


URL = '/product'


@pytest.mark.skip('TODO: need create mock file upload')
async def test_add_new_image_file_in_product(mocker: MockerFixture, db: Session) -> None:
    """Must add product in new cart and return cart."""
    # Arrange
    product_id = None
    with db:
        category = CategoryFactory()
        config_fee = CreditCardFeeConfigFactory()
        db.add_all([category, config_fee])
        db.flush()
        product_db= ProductDBFactory(
            category=category,
            installment_config=config_fee,
        )
        db.add(product_db)
        db.commit()
        product_id = product_db.product_id

    # Act
    async with AsyncClient(app=app, base_url='http://test') as client:
        response = await client.post(
            f'{URL}/upload-image/{product_id}',
            headers={"Content-Type": "multipart/form-data"},
        )

    # Assert
    assert response.status_code == 200
    assert response.json()
