from datetime import datetime
from sqlalchemy import update

from sqlalchemy.orm import SessionTransaction
from sqlalchemy.orm.exc import NoResultFound
from loguru import logger

from sqlalchemy.sql import select

from app.entities.cart import CartPayment
from app.entities.payment import PaymentDBUpdate
from app.infra.constants import PaymentMethod, PaymentStatus
from app.infra.models import CustomerDB, PaymentDB


async def create_payment(
    cart: CartPayment,
    *,
    user_id: int,
    order_id: int,
    payment_gateway: str,
    authorization: str,
    gateway_payment_id: int | str,
    transaction: SessionTransaction,
) -> PaymentDB:
    """Create a new order."""
    _freight_amount = cart.total - cart.subtotal
    order = PaymentDB(
        user_id=user_id,
        order_id=order_id,
        amount=cart.total,
        amount_with_fee=cart.total_with_fee,
        token=cart.card_token if cart.card_token else cart.pix_qr_code,
        status=PaymentStatus.PENDING.value,
        authorization=authorization,
        payment_method=cart.payment_method,
        payment_gateway=payment_gateway,
        gateway_payment_id=gateway_payment_id,
        installments=cart.installments,
        freight_amount=_freight_amount,
    )

    transaction.session.add(order)
    await transaction.session.flush()
    return order


async def get_payment_by_id(
    payment_id: int,
    *,
    transaction: SessionTransaction,
) -> PaymentDB:
    """Get an payment by its id."""
    payment_query = select(PaymentDB).where(
        PaymentDB.payment_id == payment_id,
    )
    return await transaction.session.scalar(payment_query)


async def update_payment(
    payment_id: int,
    *,
    payment: PaymentDBUpdate,
    transaction: SessionTransaction,
) -> PaymentDB:
    """Update an existing payment."""
    update_query = (
        update(PaymentDB)
        .where(PaymentDB.payment_id == payment_id)
        .values(
            **payment.model_dump(
                exclude_unset=True,
            ),
        )
        .returning(PaymentDB)
    )
    return await transaction.session.execute(update_query)


async def get_payment_by_order_id(
    order_id: int,
    *,
    transaction: SessionTransaction,
) -> PaymentDB | None:
    """Get payment by order id or return None if not exists."""
    payment_query = select(PaymentDB).where(
        PaymentDB.order_id == order_id,
    )
    return await transaction.session.scalar(payment_query)


async def create_customer(
    *,
    user_id: int,
    customer_uuid: str,
    payment_gateway: str,
    transaction: SessionTransaction,
    payment_method: str = PaymentMethod.CREDIT_CARD.name,
    token: str = '',
    issuer_id: str = '',
    status: bool = True,
) -> CustomerDB:
    """Create a new customer."""
    customer = CustomerDB(
        user_id=user_id,
        customer_uuid=customer_uuid,
        payment_gateway=payment_gateway,
        status=status,
        payment_method=payment_method,
        token=token,
        issuer_id=issuer_id,
        created_at=datetime.now(),
    )

    transaction.session.add(customer)
    await transaction.session.flush()
    if not customer:
        msg = 'Customer not found'
        raise NoResultFound(msg)
    return customer


async def get_customer(
    user_id: int,
    *,
    payment_gateway: str,
    transaction: SessionTransaction,
) -> CustomerDB:
    """Get an customers from user by its id and payment_gateway."""
    customer_query = (
        select(CustomerDB)
        .where(CustomerDB.user_id == user_id)
        .where(CustomerDB.payment_gateway == payment_gateway)
    )
    return await transaction.session.scalar(customer_query)


async def update_payment_status(
    gateway_payment_id: int,
    *,
    payment_status: str,
    transaction: SessionTransaction,
    processed: bool = False,
) -> PaymentDB:
    """Update payment to callback."""
    update_query = (
        update(PaymentDB)
        .where(
            PaymentDB.gateway_payment_id == int(gateway_payment_id),
        )
        .values(
            status=payment_status,
            processed_at=datetime.now(),
            processed=processed,
        )
        .returning(PaymentDB)
    )
    payment_update = await transaction.session.execute(update_query)
    logger.info('payment update')
    logger.info(payment_update)
    return payment_update.fetchone()


async def get_payment(
    gateway_payment_id: int,
    *,
    transaction: SessionTransaction,
) -> PaymentDB:
    """Get payment with specific payment id."""
    payment_query = select(PaymentDB).where(
        PaymentDB.gateway_payment_id == gateway_payment_id,
    )
    return await transaction.session.scalar(payment_query)


class CreditCardConfig:
    def __init__(self, config_data) -> None:
        self.config_data = config_data

    def create_installment_config(self):
        return CreateCreditConfig(
            config_data=self.config_data,
        ).create_credit()


class CreateCreditConfig:
    def __init__(self, config_data) -> None:
        self.config_data = config_data

    def create_credit(self):
        db = get_db()
        _config = None
        with db:
            db_config = CreditCardFeeConfig(
                active_date=datetime.now(),
                fee=Decimal(self.config_data.fee),
                min_installment_with_fee=self.config_data.min_installment,
                max_installments=self.config_data.max_installment,
            )
            db.add(db_config)
            db.commit()
            return ConfigCreditCardResponse.model_validate(db_config)
