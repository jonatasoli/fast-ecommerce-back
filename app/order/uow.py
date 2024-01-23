from typing import Any

from sqlalchemy.orm import SessionTransaction
from app.entities.cart import CartPayment
from app.entities.coupon import CouponResponse
from app.infra.custom_decorators import database_uow
from app.infra.models import OrderDB
from app.order import repository as order_repository
from app.order.entities import OrderDBUpdate


@database_uow()
async def uow_create_order(
    cart: CartPayment,
    *,
    affiliate_id: int | None,
    coupon: CouponResponse | None,
    user: Any,
    bootstrap: Any,
    transaction: SessionTransaction | None,
) -> int:
    """Create a new order."""
    if not transaction:
        msg = 'Transaction must be provided'
        raise ValueError(msg)
    order = await order_repository.get_order_by_cart_uuid(
        cart.uuid,
        transaction=transaction,
    )

    if not order:
        order = await order_repository.create_order(
            cart,
            affiliate_id=affiliate_id,
            coupon=coupon,
            user_id=user['user_id'],
            transaction=transaction,
        )
        for item in cart.cart_items:
            await order_repository.create_order_item(
                discount_price=item.discount_price,
                order_id=order.order_id,
                price=item.price,
                product_id=item.product_id,
                quantity=item.quantity,
                transaction=transaction,
            )

    return order.order_id


@database_uow()
async def uow_update_paid_order(
    order_update: OrderDBUpdate,
    transaction: SessionTransaction | None,
    bootstrap: Any,
) -> OrderDB:
    if not transaction:
        msg = 'Transaction must be provided'
        raise ValueError(msg)

    return await order_repository.update_order(
        order_update,
        transaction=transaction,
    )


@database_uow()
async def uow_create_order_status_step(
    order_id: int,
    *,
    status: str,
    bootstrap: Any,
    transaction: SessionTransaction | None,
    send_mail: bool = False,
) -> int:
    if not transaction:
        msg = 'Transaction must be provided'
        raise ValueError(msg)
    return await order_repository.create_order_status_step(
        order_id=order_id,
        status=status,
        sending=send_mail,
        transaction=transaction,
    )
