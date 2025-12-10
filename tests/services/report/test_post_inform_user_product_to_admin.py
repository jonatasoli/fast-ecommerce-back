import pytest
from unittest.mock import AsyncMock, MagicMock

from faststream.rabbit import RabbitQueue
from app.report.tasks import task_message_bus

from app.entities.report import InformUserProduct
from app.report.services import notify_product_to_admin
from app.report import repository as report_repository
from tests.factories_db import (
    CategoryFactory,
    CreditCardFeeConfigFactory,
    InformUserProductDBFactory,
    ProductDBFactory,
)


@pytest.mark.asyncio
async def test_input_to_user_admin(mocker, asyncdb):
    # Setup
    admin_emails = ['admin1@example.com', 'admin2@example.com']
    mock_get_admins = mocker.patch(
        'app.report.repository.get_admins',
        new_callable=AsyncMock,
        return_value=admin_emails,
    )
    mock_get_product = mocker.patch(
        'app.product.repository.get_product_by_id',
        new_callable=AsyncMock,
    )
    credit_card_config = CreditCardFeeConfigFactory()
    category = CategoryFactory()
    product = None
    db = asyncdb
    async with db() as transaction:
        transaction.add(category)
        transaction.add(credit_card_config)
        await transaction.flush()
        product = ProductDBFactory(
            category=category,
            installment_config=credit_card_config,
        )
        transaction.add(product)
        await transaction.commit()
    product.quantity = 10
    mock_get_product.return_value = product
    mock_inform = InformUserProductDBFactory(
        product_id=product.product_id,
        product_name=product.name,
        user_mail='email@email.com',
        user_phone='1234567890',
    )
    mock_get_product = mocker.patch.object(
        report_repository,
        'save_user_inform',
        return_value=mock_inform,
    )
    mock_broker_publish = mocker.patch.object(
        task_message_bus.broker,
        'publish',
        new_callable=AsyncMock,
    )
    mock_transaction = mocker.patch('sqlalchemy.ext.asyncio.AsyncSession.begin')
    mock_transaction.__aenter__ = MagicMock()
    mock_transaction.__aexit__ = MagicMock()
    inform = InformUserProduct(
        email='email@email.com',
        phone='1234567890',
        product_id=product.product_id,
    )

    # Act
    await notify_product_to_admin(
        inform=inform,
        db=db,
        broker=mock_broker_publish,
    )

    mock_get_admins.assert_called_once()
    mock_get_product.assert_called_once()
    mock_broker_publish.publish.assert_called_once_with(
        {
            'admin_email': admin_emails,
            'product_id': inform.product_id,
            'product_name': product.name,
            'user_email': inform.email,
            'user_phone': inform.phone,
        },
        queue=RabbitQueue('inform_product_to_admin'),
    )
