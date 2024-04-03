from typing import Any
from fastapi import Depends

from loguru import logger
from app.entities.cart import CartPayment
from app.infra.bootstrap.task_bootstrap import Command, bootstrap
from app.infra.constants import PaymentGatewayAvailable
from app.infra.worker import task_message_bus


async def get_bootstrap() -> Command:
    """Get bootstrap."""
    return await bootstrap()


async def create_pending_payment(
    order_id: int,
    *,
    cart: CartPayment,
    authorization: str,
    payment_gateway: str,
    gateway_payment_id: int | str,
    user_id: int,
    bootstrap: Any,
) -> int:
    """Create a new payment."""
    return await bootstrap.payment_uow.uow_create_pending_payment(
        order_id,
        cart=cart,
        user_id=user_id,
        authorization=authorization,
        payment_gateway=payment_gateway,
        gateway_payment_id=gateway_payment_id,
        bootstrap=bootstrap,
    )


async def update_payment(
    payment_id: int,
    payment_status: str,
    authorization: str,
    payment_gateway: str,
    processed: bool,
    bootstrap: Any,
):
    """Update payment status."""
    await bootstrap.payment_uow.uow_update_payment(
        payment_id,
        payment_status=payment_status,
        authorization=authorization,
        payment_gateway=payment_gateway,
        processed=processed,
        bootstrap=bootstrap,
    )


@task_message_bus.subscriber('create_customer')
async def create_customer(
    user_id: int,
    user_email: str,
    bootstrap: Any = Depends(get_bootstrap),
) -> None:
    """Create a customer in stripe and mercado pago."""
    customers = bootstrap.payment.create_customer_in_gateway(
        user_email=user_email,
    )
    customers_ids = []
    for payment_gateway in PaymentGatewayAvailable:
        id = await bootstrap.payment_uow.uow_create_customer(
            user_id,
            customer_id=customers[payment_gateway.value]['id'],
            payment_gateway=payment_gateway.value,
            bootstrap=bootstrap,
        )
        customers_ids.append(id)
    for customer in customers_ids:
        logger.info(f'Customer {customer} from {user_id} created with success')
