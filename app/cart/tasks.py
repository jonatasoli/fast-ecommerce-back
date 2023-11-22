# ruff:  noqa: D202 D205 T201 D212
from typing import Any, Self
from fastapi import Depends
from app.infra.constants import OrderStatus, PaymentMethod

from propan.brokers.rabbit import RabbitQueue

from app.infra.models.order import Coupons
from app.inventory.tasks import decrease_inventory
from app.order.entities import (
    CreateOrderStatusStepError,
    OrderDBUpdate,
    OrderNotFound,
)
from loguru import logger

from app.entities.cart import CartPayment
from app.infra.payment_gateway.stripe_gateway import (
    PaymentGatewayRequestError,
)

from app.infra.bootstrap.task_bootstrap import bootstrap, Command
from app.order.tasks import (
    create_order,
    create_order_status_step,
    update_order,
)
from app.payment.entities import CreatePaymentError, PaymentAcceptError
from app.payment.tasks import create_pending_payment, update_payment
from app.infra.worker import task_message_bus


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


@task_message_bus.event('checkout')
async def checkout(
    cart_uuid: str,
    payment_method: str,
    payment_gateway: str,
    user: Any,
    bootstrap: Any = Depends(get_bootstrap),
) -> dict:
    """Checkout cart with payment intent."""
    _ = payment_method
    order_id = None
    logger.info(
        f'Checkout cart start{cart_uuid} with gateway {payment_gateway} with success',
    )
    try:
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
                products_db = await bootstrap.cart_repository.get_products(
                    products=cart.cart_items,
                    transaction=session,
                )
                cart.get_products_price_and_discounts(products_db)
        cart.calculate_subtotal(discount=coupon.discount if cart.coupon else 0)

        match cart.payment_method:
            case (PaymentMethod.CREDIT_CARD.value):
                payment_response = (
                    bootstrap.payment.create_credit_card_payment(
                        payment_gateway=cart.gateway_provider,
                        customer_id=cart.customer_id,
                        amount=cart.subtotal,
                        card_token=cart.card_token,
                        installments=cart.installments,
                    )
                )
                payment_id, order_id = await create_pending_payment_and_order(
                    cart=cart,
                    affiliate=affiliate,
                    coupon=coupon,
                    user=user,
                    payment_gateway=cart.gateway_provider,
                    gateway_payment_id=payment_response.id,
                    authorization=payment_response.authorization_code,
                    bootstrap=bootstrap,
                )
                cart.payment_intent = payment_response.id
                authorization = payment_response.authorization_code
                payment_accept = bootstrap.payment.accept_payment(
                    payment_gateway=cart.gateway_provider,
                    payment_id=cart.payment_intent,
                )

                logger.info(f'Payment response: {payment_accept}')

                # TODO: check if order is in inventory for decrease
                await decrease_inventory(
                    cart=cart,
                    order_id=order_id,
                    bootstrap=bootstrap,
                )
                if payment_accept.status == 'approved':
                    await update_order(
                        order_update=OrderDBUpdate(
                            order_id=order_id,
                            order_status=OrderStatus.PAYMENT_PAID.value,
                            customer_id=cart.customer_id,
                        ),
                        bootstrap=bootstrap,
                    )
                    payment_id = await update_payment(
                        payment_id=payment_id,
                        payment_gateway=cart.gateway_provider,
                        authorization=authorization,
                        payment_status=payment_accept.status,
                        processed=True,
                        bootstrap=bootstrap,
                    )
                    await create_order_status_step(
                        order_id=order_id,
                        status=OrderStatus.PAYMENT_PAID.value,
                        send_mail=True,
                        bootstrap=bootstrap,
                    )
                logger.info(
                    f'Checkout cart {cart_uuid} with payment {payment_id} processed with success',
                )
            case (PaymentMethod.PIX.value):
                payment_id, order_id = await create_pending_payment_and_order(
                    cart=cart,
                    affiliate=affiliate,
                    coupon=coupon,
                    payment_gateway=cart.gateway_provider,
                    user=user,
                    gateway_payment_id=cart.pix_payment_id,
                    bootstrap=bootstrap,
                )
                logger.info(
                    f'Checkout cart {cart_uuid} with payment {payment_id} concluded with success',
                )
            case (_):
                raise Exception('Payment method not found')

        bootstrap.cache.delete(cart_uuid)
    except PaymentAcceptError:
        await bootstrap.message.broker.publish(
            {
                'mail_to': user['email'],
                'order_id': order_id if order_id else '',
                'reason': 'Dados do cartão incorreto ou sem limite disponível',
            },
            queue=RabbitQueue('notification_order_cancelled'),
        )
        return PAYMENT_STATUS_ERROR_MESSAGE
    except PaymentGatewayRequestError:
        await bootstrap.message.broker.publish(
            {
                'mail_to': user['email'],
                'order_id': order_id if order_id else '',
                'reason': 'Erro quando foi chamado o emissor do cartão tente novamente mais tarde',
            },
            queue=RabbitQueue('notification_order_cancelled'),
        )
        return PAYMENT_REQUEST_ERROR_MESSAGE
    except Exception as e:
        logger.error(f'Error in checkout: {e}')
        await bootstrap.message.broker.publish(
            {
                'mail_to': user['email'],
                'order_id': order_id if order_id else '',
                'reason': 'Erro desconhecido favor entre em contato conosco',
            },
            queue=RabbitQueue('notification_order_cancelled'),
        )
        raise
    return {'order_id': {order_id}, 'message': 'processed'}


async def create_pending_payment_and_order(
    cart: CartPayment,
    affiliate: str | None,
    coupon: Coupons | None,
    user: Any,
    payment_gateway: str,
    gateway_payment_id: int,
    bootstrap: Any,
    authorization: str = 'PENDING',
) -> tuple[int, int]:
    """Create pending payment and order."""
    try:
        order_id = await create_order(
            cart=cart,
            affiliate=affiliate,
            discount=coupon.discount if cart.coupon else 0,
            user=user,
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
            user_id=user['user_id'],
            authorization=authorization,
            payment_gateway=payment_gateway,
            gateway_payment_id=gateway_payment_id,
            bootstrap=bootstrap,
        )
        if not payment_id:
            msg = f'Is not possible create payment with order {order_id}'
            raise CreatePaymentError(
                msg,
            )
        order_status_step_id = await create_order_status_step(
            order_id=order_id,
            status='pending',
            bootstrap=bootstrap,
        )
        if not order_status_step_id:
            msg = f'Is not possible create order_status_step with order {order_id}'
            raise CreateOrderStatusStepError(
                msg,
            )

        await bootstrap.message.broker.publish(
            {
                'mail_to': user['email'],
                'order_id': order_id if order_id else '',
            },
            queue=RabbitQueue('notification_order_processed'),
        )

        return payment_id, order_id
    except Exception as e:
        logger.error(f'Error in create pending payment and order: {e}')
        raise
