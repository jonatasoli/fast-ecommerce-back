from sqlalchemy import update

from sqlalchemy.orm import SessionTransaction

from sqlalchemy.sql import select

from app.entities.cart import CartPayment
from app.entities.payment import PaymentGateway, PaymentDBUpdate
from app.infra.constants import PaymentStatus
from app.infra.models.transaction import Payment


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
