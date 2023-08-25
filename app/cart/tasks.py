# ruff:  noqa: D202 D205 T201 D212
from typing import Any
from app.entities.payment import PaymentGateway, validate_payment
from app.inventory.tasks import decrease_inventory
from app.order.entities import CreateOrderStatusStepError, OrderNotFound
from loguru import logger

from app.entities.cart import CartPayment
from app.infra.stripe import confirm_payment_intent
from config import settings

from app.infra.bootstrap.task_bootstrap import bootstrap, Command
from app.infra.worker import task_cart_router
from app.order.tasks import (
    create_order,
    create_order_status_step,
    update_order,
)
from app.payment.entities import CreatePaymentError, PaymentAcceptError
from app.payment.tasks import create_pending_payment, update_payment_status


@task_cart_router.event('checkout')
async def checkout(
    cart_uuid: str, payment_intent: str, bootstrap: Command
) -> None:
    """Checkout cart with payment intent."""
    cache = bootstrap.cache
    cache_cart = cache.get(cart_uuid)
    if not cache_cart:
        raise Exception('Cart not found')
    cart = CartPayment.model_validate_json(cache_cart)
    affiliate = cart.affiliate if cart.affiliate else None
    coupon = cart.coupon if cart.coupon else None
    if coupon:
        with bootstrap.db() as session:
            coupon = bootstrap.cart_repository.get_coupon_by_code(
                session, coupon
            )
    cart.calculate_subtotal(discount=coupon.coupon_fee if cart.coupon else 0)
    order_id = create_order(cart=cart, affiliate=affiliate, coupon=coupon)
    if not order_id:
        raise OrderNotFound(
            f'Is not possible create order with cart {cart.uuid}'
        )
    payment_id = create_pending_payment(
        order_id=order_id, payment_intent=payment_intent
    )
    if not payment_id:
        raise CreatePaymentError(
            f'Is not possible create payment with order {order_id}'
        )
    order_status_step_id = create_order_status_step(
        order_id=order_id, status='pending'
    )
    if not order_status_step_id:
        raise CreateOrderStatusStepError(
            f'Is not possible create order_status_step with order {order_id}'
        )
    payment_accept = confirm_payment_intent(
        payment_intent_id=payment_intent['id'],
        payment_method=payment_intent['payment_method'],
        receipt_email='contact@jonatasoliveira.dev',
    )
    if payment_accept['error']:
        raise PaymentAcceptError(payment_accept['error'])
    status = validate_payment(
        payment_accept, PaymentGateway[settings.PATMENT_GATEWAY]
    )
    if not status == 'succeeded':
        return

    decrease_inventory(cart=cart)
    update_order(order_id=order_id, order_status='paid')
    update_payment_status(payment_id=payment_id, payment_status='paid')
    create_order_status_step(
        order_status_step_id=order_status_step_id,
        status='paid',
        send_mail=True,
    )
    logger.info(
        f'Checkout cart {cart_uuid} with payment {payment_id} concluded with success'
    )
