"""Additional tests for report/services.py to achieve 100% coverage."""
import pytest
from decimal import Decimal
from datetime import datetime, timedelta, UTC
from faker import Faker

from app.entities.report import CommissionInDB, UserSalesCommissions
from app.infra.constants import FeeType
from app.infra.models import SalesCommissionDB
from app.report.services import (
    get_user_sales_commissions,
    get_sales_commissions,
    create_sales_commission,
)
from tests.factories_db import CreditCardFeeConfigFactory

fake = Faker()


@pytest.mark.asyncio
async def test_get_user_sales_commissions_should_return_commissions(mocker, asyncdb):
    """Must return user sales commissions."""
    # Arrange
    user = {"user_id": fake.random_int()}
    paid = fake.pybool()
    released = fake.pybool()
    
    expected_commissions = [
        CommissionInDB(
            commission_id=fake.random_int(),
            order_id=fake.random_int(),
            user_id=user["user_id"],
            commission=Decimal(fake.pydecimal(left_digits=4, right_digits=2, min_value=10, max_value=1000)),
            date_created=datetime.now(UTC),
            release_date=datetime.now(UTC) + timedelta(days=30),
            paid=paid,
            payment_id=fake.random_int(),
        )
    ]
    
    mock_repo = mocker.patch(
        "app.report.repository.get_user_sales_commissions",
        return_value=expected_commissions,
    )
    
    # Act
    result = await get_user_sales_commissions(user, paid=paid, released=released, db=asyncdb)
    
    # Assert
    mock_repo.assert_called_once()
    assert result == expected_commissions


@pytest.mark.asyncio
async def test_get_sales_commissions_should_return_all_commissions(mocker, asyncdb):
    """Must return all sales commissions."""
    # Arrange
    paid = fake.pybool()
    released = fake.pybool()
    
    # Create mock result with unique() and all() methods
    mock_result = mocker.MagicMock()
    mock_result.unique.return_value.all.return_value = [
        {
            "commission_id": fake.random_int(),
            "order_id": fake.random_int(),
            "user_id": fake.random_int(),
            "commission": Decimal("100.50"),
            "date_created": datetime.now(UTC),
            "release_date": datetime.now(UTC) + timedelta(days=30),
            "paid": paid,
            "payment_id": fake.random_int(),
        }
    ]
    
    mock_repo = mocker.patch(
        "app.report.repository.get_sales_commissions",
        return_value=mock_result,
    )
    
    # Act
    result = await get_sales_commissions(paid=paid, released=released, db=asyncdb)
    
    # Assert
    mock_repo.assert_called_once()
    assert isinstance(result, UserSalesCommissions)
    assert len(result.commissions) > 0


@pytest.mark.asyncio
async def test_create_sales_commission_with_percentage_fees(mocker, asyncdb):
    """Must create sales commission with percentage fees."""
    # Arrange
    order_id = fake.random_int()
    user_id = fake.random_int()
    subtotal = Decimal("1000.00")
    commission_percentage = Decimal("0.10")
    payment_id = fake.random_int()
    
    # Mock campaign
    mock_campaign = None
    mocker.patch(
        "app.campaign.repository.get_campaign",
        return_value=mock_campaign,
    )
    
    # Mock fees with percentage type
    mock_fee = mocker.MagicMock()
    mock_fee.fee_type = FeeType.PERCENTAGE
    mock_fee.value = Decimal("0.05")  # 5%
    
    mocker.patch(
        "app.report.repository.get_fees",
        return_value=[mock_fee],
    )
    
    # Mock co-producers
    mocker.patch(
        "app.report.repository.get_coproducer",
        return_value=None,
    )
    
    # Mock session
    mock_transaction = mocker.MagicMock()
    mock_transaction.add = mocker.MagicMock()
    mock_transaction.commit = mocker.MagicMock()
    mock_context = mocker.MagicMock()
    mock_context.__enter__ = mocker.MagicMock(return_value=mock_transaction)
    mock_context.__exit__ = mocker.MagicMock(return_value=None)
    mock_db_instance = mocker.MagicMock()
    mock_db_instance.begin = mocker.MagicMock(return_value=mock_context)
    mock_db = mocker.MagicMock(return_value=mock_db_instance)
    
    # Act
    result = await create_sales_commission(
        order_id=order_id,
        user_id=user_id,
        subtotal=subtotal,
        commission_percentage=commission_percentage,
        payment_id=payment_id,
        db=mock_db,
        async_db=asyncdb,
    )
    
    # Assert
    assert isinstance(result, SalesCommissionDB)
    assert result.order_id == order_id
    assert result.user_id == user_id
    mock_transaction.add.assert_called_once()
    mock_transaction.commit.assert_called_once()


@pytest.mark.asyncio
async def test_create_sales_commission_with_fixed_fees(mocker, asyncdb):
    """Must create sales commission with fixed fees."""
    # Arrange
    order_id = fake.random_int()
    user_id = fake.random_int()
    subtotal = Decimal("1000.00")
    commission_percentage = Decimal("0.10")
    payment_id = fake.random_int()
    
    # Mock campaign
    mock_campaign = None
    mocker.patch(
        "app.campaign.repository.get_campaign",
        return_value=mock_campaign,
    )
    
    # Mock fees with fixed type
    mock_fee = mocker.MagicMock()
    mock_fee.fee_type = FeeType.FIXED
    mock_fee.value = Decimal("50.00")
    
    mocker.patch(
        "app.report.repository.get_fees",
        return_value=[mock_fee],
    )
    
    # Mock co-producers
    mocker.patch(
        "app.report.repository.get_coproducer",
        return_value=None,
    )
    
    # Mock session
    mock_transaction = mocker.MagicMock()
    mock_transaction.add = mocker.MagicMock()
    mock_transaction.commit = mocker.MagicMock()
    mock_context = mocker.MagicMock()
    mock_context.__enter__ = mocker.MagicMock(return_value=mock_transaction)
    mock_context.__exit__ = mocker.MagicMock(return_value=None)
    mock_db_instance = mocker.MagicMock()
    mock_db_instance.begin = mocker.MagicMock(return_value=mock_context)
    mock_db = mocker.MagicMock(return_value=mock_db_instance)
    
    # Act
    result = await create_sales_commission(
        order_id=order_id,
        user_id=user_id,
        subtotal=subtotal,
        commission_percentage=commission_percentage,
        payment_id=payment_id,
        db=mock_db,
        async_db=asyncdb,
    )
    
    # Assert
    assert isinstance(result, SalesCommissionDB)
    mock_transaction.add.assert_called_once()


@pytest.mark.asyncio
async def test_create_sales_commission_with_coproducers(mocker, asyncdb):
    """Must create salescommission with co-producer fees."""
    # Arrange
    order_id = fake.random_int()
    user_id = fake.random_int()
    subtotal = Decimal("1000.00")
    commission_percentage = Decimal("0.10")
    payment_id = fake.random_int()
    
    # Mock campaign
    mock_campaign = None
    mocker.patch(
        "app.campaign.repository.get_campaign",
        return_value=mock_campaign,
    )
    
    # Mock fees
    mocker.patch(
        "app.report.repository.get_fees",
        return_value=[],
    )
    
    # Mock co-producers with percentage
    mock_co_producer = mocker.MagicMock()
    mock_co_producer.percentage = Decimal("10")  # 10%
    
    mocker.patch(
        "app.report.repository.get_coproducer",
        return_value=[mock_co_producer],
    )
    
    # Mock session
    mock_transaction = mocker.MagicMock()
    mock_transaction.add = mocker.MagicMock()
    mock_transaction.commit = mocker.MagicMock()
    mock_context = mocker.MagicMock()
    mock_context.__enter__ = mocker.MagicMock(return_value=mock_transaction)
    mock_context.__exit__ = mocker.MagicMock(return_value=None)
    mock_db_instance = mocker.MagicMock()
    mock_db_instance.begin = mocker.MagicMock(return_value=mock_context)
    mock_db = mocker.MagicMock(return_value=mock_db_instance)
    
    # Act
    result = await create_sales_commission(
        order_id=order_id,
        user_id=user_id,
        subtotal=subtotal,
        commission_percentage=commission_percentage,
        payment_id=payment_id,
        db=mock_db,
        async_db=asyncdb,
    )
    
    # Assert
    assert isinstance(result, SalesCommissionDB)
    mock_transaction.add.assert_called_once()


@pytest.mark.asyncio
async def test_create_sales_commission_without_percentage_should_raise(mocker, asyncdb):
    """Must raise ValueError when commission_percentage is None."""
    # Arrange
    order_id = fake.random_int()
    user_id = fake.random_int()
    subtotal = Decimal("1000.00")
    commission_percentage = None
    payment_id = fake.random_int()
    
    # Mock campaign
    mocker.patch(
        "app.campaign.repository.get_campaign",
        return_value=None,
    )
    
    # Mock fees
    mocker.patch(
        "app.report.repository.get_fees",
        return_value=[],
    )
    
    # Mock co-producers
    mocker.patch(
        "app.report.repository.get_coproducer",
        return_value=None,
    )
    
    # Mock session
    mock_transaction = mocker.MagicMock()
    mock_context = mocker.MagicMock()
    mock_context.__enter__ = mocker.MagicMock(return_value=mock_transaction)
    mock_context.__exit__ = mocker.MagicMock(return_value=None)
    mock_db_instance = mocker.MagicMock()
    mock_db_instance.begin = mocker.MagicMock(return_value=mock_context)
    mock_db = mocker.MagicMock(return_value=mock_db_instance)
    
    # Act / Assert
    with pytest.raises(ValueError, match="Error with percentage in report"):
        await create_sales_commission(
            order_id=order_id,
            user_id=user_id,
            subtotal=subtotal,
            commission_percentage=commission_percentage,
            payment_id=payment_id,
            db=mock_db,
            async_db=asyncdb,
        )


@pytest.mark.asyncio
async def test_create_sales_commission_with_campaign(mocker, asyncdb):
    """Must create sales commission with campaign fee."""
    # Arrange
    order_id = fake.random_int()
    user_id = fake.random_int()
    subtotal = Decimal("1000.00")
    commission_percentage = Decimal("0.10")
    payment_id = fake.random_int()
    
    # Mock campaign with min purchase value
    mock_campaign = mocker.MagicMock()
    mock_campaign.min_purchase_value = Decimal("500.00")
    mock_campaign.commission_fee_value = Decimal("20.00")
    
    mocker.patch(
        "app.campaign.repository.get_campaign",
        return_value=mock_campaign,
    )
    
    # Mock fees
    mocker.patch(
        "app.report.repository.get_fees",
        return_value=[],
    )
    
    # Mock co-producers
    mocker.patch(
        "app.report.repository.get_coproducer",
        return_value=None,
    )
    
    # Mock session
    mock_transaction = mocker.MagicMock()
    mock_transaction.add = mocker.MagicMock()
    mock_transaction.commit = mocker.MagicMock()
    mock_context = mocker.MagicMock()
    mock_context.__enter__ = mocker.MagicMock(return_value=mock_transaction)
    mock_context.__exit__ = mocker.MagicMock(return_value=None)
    mock_db_instance = mocker.MagicMock()
    mock_db_instance.begin = mocker.MagicMock(return_value=mock_context)
    mock_db = mocker.MagicMock(return_value=mock_db_instance)
    
    # Act
    result = await create_sales_commission(
        order_id=order_id,
        user_id=user_id,
        subtotal=subtotal,
        commission_percentage=commission_percentage,
        payment_id=payment_id,
        db=mock_db,
        async_db=asyncdb,
    )
    
    # Assert
    assert isinstance(result, SalesCommissionDB)
    mock_transaction.add.assert_called_once()
