from contextlib import suppress
from typing import Any
from app.infra.models import PaymentDB

from sqlalchemy.orm import SessionTransaction
from app.entities.cart import CartPayment
from app.entities.payment import CustomerInDB, PaymentDBUpdate,CustomerNotFoundError
from app.infra.custom_decorators import database_uow
from app.payment import repository as payment_repository


@database_uow()
async def uow_create_pending_payment(
    order_id: int,
    *,
    cart: CartPayment,
    user_id: int,
    authorization: str,
    payment_gateway: str,
    bootstrap: Any,
    gateway_payment_id: int | str,
    transaction: SessionTransaction | None,
) -> int:
    """Create a new payment."""
    if not transaction:
        msg = 'Transaction must be provided'
        raise ValueError(msg)
    payment = await payment_repository.get_payment_by_order_id(
        order_id,
        transaction=transaction,
    )
    if not payment:
        payment = await payment_repository.create_payment(
            cart,
            order_id=order_id,
            user_id=user_id,
            authorization=authorization,
            payment_gateway=payment_gateway,
            gateway_payment_id=gateway_payment_id,
            transaction=transaction,
        )
    return payment.payment_id


@database_uow()
async def uow_update_payment(
    payment_id: int,
    *,
    payment_status: str,
    authorization: str,
    payment_gateway: str,
    bootstrap: Any,
    transaction: SessionTransaction | None,
    processed: bool = False,
) -> PaymentDB:
    """Update payment status."""
    if not transaction:
        msg = 'Transaction must be provided'
        raise ValueError(msg)
    return await payment_repository.update_payment(
        payment_id,
        payment=PaymentDBUpdate(
            status=payment_status,
            authorization=authorization,
            processed=processed,
            payment_gateway=payment_gateway,
        ),
        transaction=transaction,
    )


@database_uow()
async def uow_create_customer(
    user_id: int,
    *,
    customer_id: str,
    payment_gateway: str,
    bootstrap: Any,
    transaction: SessionTransaction | None,
) -> CustomerInDB | None:
    """Create a new customer."""
    if not transaction:
        msg = 'Transaction must be provided'
        raise ValueError(msg)
    customer_db = None
    with suppress(CustomerNotFoundError):
        customer_db = await payment_repository.get_customer(
            user_id,
            payment_gateway=payment_gateway,
            transaction=transaction,
        )
    if not customer_db:
        customer_db = await payment_repository.create_customer(
            user_id=user_id,
            customer_uuid=customer_id,
            payment_gateway=payment_gateway,
            transaction=transaction,
        )
    customer_id = CustomerInDB.model_validate(customer_db)


@database_uow()
async def uow_update_gateway_payment_status(
    payment_id: int,
    *,
    payment_status: str,
    authorization: str,
    payment_gateway: str,
    gateway_payment_id: int | str,
    bootstrap: Any,
    transaction: SessionTransaction | None,
) -> None:
    """Update payment status."""
    if not transaction:
        msg = 'Transaction must be provided'
        raise ValueError(msg)
    await payment_repository.update_gateway_payment(
        payment_id,
        payment=PaymentDBUpdate(
            status=payment_status,
            authorization=authorization,
            payment_gateway=payment_gateway,
            gateway_payment_id=gateway_payment_id,
        ),
        transaction=transaction,
    )
