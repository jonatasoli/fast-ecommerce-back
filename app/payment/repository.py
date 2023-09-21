from datetime import datetime
from sqlalchemy import update

from sqlalchemy.orm import SessionTransaction

from sqlalchemy.sql import select

from app.entities.cart import CartPayment
from app.entities.payment import PaymentGateway, PaymentDBUpdate
from app.infra.constants import PaymentMethod, PaymentStatus
from app.infra.models.transaction import Customer, Payment


async def create_payment(
    cart: CartPayment,
    *,
    user_id: int,
    order_id: int,
    transaction: SessionTransaction,
) -> Payment:
    """Create a new order."""
    order = Payment(
        user_id=user_id,
        order_id=order_id,
        amount=cart.subtotal,
        token=cart.payment_intent,
        gateway_id=1,
        status=PaymentStatus.PENDING.value,
        authorization=cart.payment_intent,
        payment_method=cart.payment_method_id,
        payment_gateway=PaymentGateway.STRIPE.name,
        installments=cart.installments,
    )

    transaction.session.add(order)
    await transaction.session.flush()
    return order


async def get_payment_by_id(
    payment_id: int,
    *,
    transaction: SessionTransaction,
) -> Payment:
    """Get an payment by its id."""
    payment_query = select(Payment).where(
        Payment.payment_id == payment_id,
    )
    return await transaction.session.scalar(payment_query)


async def update_payment(
    payment_id: int,
    *,
    payment: PaymentDBUpdate,
    transaction: SessionTransaction,
) -> Payment:
    """Update an existing payment."""
    update_query = (
        update(Payment)
        .where(Payment.payment_id == payment_id)
        .values(
            **payment.model_dump(
                exclude_unset=True,
            ),
        )
        .returning(Payment)
    )
    return await transaction.session.execute(update_query)


async def get_payment_by_order_id(
    order_id: int,
    *,
    transaction: SessionTransaction,
) -> Payment | None:
    """Get payment by order id or return None if not exists."""
    payment_query = select(Payment).where(
        Payment.order_id == order_id,
    )
    return await transaction.session.scalar(payment_query)


async def create_customer(
    *,
    user_id: int,
    customer_uuid: str,
    payment_gateway: str,
    payment_method: str = PaymentMethod.CREDIT_CARD.name,
    token: str = '',
    issuer_id: str = '',
    status: bool = True,
    transaction: SessionTransaction,
) -> Customer:
    """Create a new customer."""
    customer = Customer(
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
    return customer


async def get_customer(
    user_id: int,
    *,
    payment_gateway: str,
    transaction: SessionTransaction,
) -> Customer:
    """Get an customers from user by its id and payment_gateway."""
    customer_query = select(Customer).where(Customer.user_id == user_id).where(Customer.payment_gateway == payment_gateway)
    return await transaction.session.scalar(customer_query)
