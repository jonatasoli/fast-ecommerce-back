
from fastapi import status
import pytest

from tests.factories_db import CategoryFactory, CreditCardFeeConfigFactory, InventoryDBFactory, ProductDBFactory


URL = '/catalog'


@pytest.mark.asyncio
def test_empty_data_should_return_200(client):
    """Must return empty list."""
    # Act
    response = client.get(f'{URL}/showcase/all')

    # Assert
    assert response.status_code == status.HTTP_200_OK

@pytest.mark.asyncio
def test_with_product_showcase_option_should_list(client, db):
    """Must return product with showcase option."""
    # Arrange
    with db() as transaction:
        category = CategoryFactory()
        config_fee = CreditCardFeeConfigFactory()
        transaction.add_all([category, config_fee])
        transaction.flush()
        product_db_1 = ProductDBFactory(
            category=category,
            installment_config=config_fee,
            price=100,
            showcase=True,
            active=True,
        )
        product_db_2 = ProductDBFactory(
            category=category,
            installment_config=config_fee,
            price=200,
            active=True,
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
        transaction.add_all([product_db_1, product_db_2])
        transaction.flush()
        transaction.add_all([inventory_db_1, inventory_db_2])
        transaction.commit()

    # Act
    response = client.get(f'{URL}/showcase/all')

    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert response.json()[0].get('product_id') == product_db_1.product_id


