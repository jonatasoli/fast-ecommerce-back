# ruff:  noqa: D202 D205 T201 D212
from typing import Any, Self
from fastapi import Depends
from app.entities.user import UserDBGet
from app.infra.constants import OrderStatus, PaymentStatus
from app.infra.models.users import User
from config import settings

from app.entities.payment import PaymentGateway, validate_payment
from app.inventory.tasks import decrease_inventory
from app.order.entities import CreateOrderStatusStepError, OrderDBUpdate, OrderNotFound
from loguru import logger

from app.entities.cart import CartPayment
from app.infra.stripe import PaymentGatewayRequestError, confirm_payment_intent
from config import settings

from app.infra.bootstrap.task_bootstrap import bootstrap, Command
from app.order.tasks import (
    create_order,
    create_order_status_step,
    update_order,
)
from app.payment.entities import CreatePaymentError, PaymentAcceptError
from app.payment.tasks import create_pending_payment, update_payment
from app.infra.worker import task_cart_router
from domains.domain_mail import send_mail


PAYMENT_STATUS_ERROR_MESSAGE = 'This payment intent is not paid yet'
PAYMENT_REQUEST_ERROR_MESSAGE = (
    'This payment intent with problem in request or already accepted'
)


class PaymentStatusError(Exception):
    """Payment accept error."""

    def __init__(self: Self) -> None:
        super().__init__('Payment status is not payed yet')


async def get_bootstrap() -> Command:
    """Get bootstrap."""
    return await bootstrap()


@task_cart_router.event('checkout')
async def checkout(
    cart_uuid: str,
    payment_intent: str,
    payment_method: str,
    user: Any,
    bootstrap: Any = Depends(get_bootstrap),
) -> str:
    """Checkout cart with payment intent."""
    logger.info(
        f'Checkout cart start{cart_uuid} with intent {payment_intent} concluded with success',
    )
    try:
        import ipdb; ipdb.set_trace()
        cache = bootstrap.cache
        cache_cart = cache.get(cart_uuid)
        if not cache_cart:
            msg = 'Cart not found'
            raise Exception(msg)
        cart = CartPayment.model_validate_json(cache_cart)
        affiliate = cart.affiliate if cart.affiliate else None
        coupon = cart.coupon if cart.coupon else None
        if coupon:
            with bootstrap.db() as session:
                coupon = bootstrap.cart_repository.get_coupon_by_code(
                    session,
                    coupon,
                )
        cart.calculate_subtotal(discount=coupon.discount if cart.coupon else 0)
        order_id = await create_order(
            cart=cart,
            affiliate=affiliate,
            discount=coupon.discount if cart.coupon else 0,
            bootstrap=bootstrap,
        )
        if not order_id:
            msg = f'Is not possible create order with cart {cart.uuid}'
            raise OrderNotFound(
                msg,
            )
        payment_id = await create_pending_payment(
            order_id=order_id,
            cart=cart,
            user_id=user.user_id,
        )
        if not payment_id:
            msg = f'Is not possible create payment with order {order_id}'
            raise CreatePaymentError(
                msg,
            )
        order_status_step_id = await create_order_status_step(
            order_id=order_id,
            status='pending',
        )
        if not order_status_step_id:
            msg = f'Is not possible create order_status_step with order {order_id}'
            raise CreateOrderStatusStepError(
                msg,
            )
        payment_accept = confirm_payment_intent(
            payment_intent_id=payment_intent,
            payment_method=payment_method,
            receipt_email=user.email,
        )
        validate_payment(
            payment_accept,
        )
        await decrease_inventory(cart=cart)
        await update_order(
                order_update=OrderDBUpdate(
                    order_id=order_id,
                    status=OrderStatus.PAYMENT_PAID,
                    customer_id=cart.customer_id
                )
        )
        payment_id = await update_payment(payment_id=payment_id, payment_status=PaymentStatus.PAID)
        await create_order_status_step(
            order_id=order_id,
            status=OrderStatus.PAYMENT_PAID,
            send_mail=True,
        )
        logger.info(
            f'Checkout cart {cart_uuid} with payment {payment_id} concluded with success',
        )
        bootstrap.cache.delete(cart_uuid)
        return f'{payment_id} is paid'
    except PaymentAcceptError:
        return PAYMENT_STATUS_ERROR_MESSAGE
    except PaymentGatewayRequestError:
        return PAYMENT_REQUEST_ERROR_MESSAGE
    except Exception as e:
        logger.error(f'Error in checkout: {e}')
        raise e
