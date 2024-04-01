# ruff:  noqa: D202 D205 T201 D212
import re
from decimal import Decimal
from typing import Any, Self

from fastapi import Depends, HTTPException
from loguru import logger
from propan.brokers.rabbit import RabbitQueue

from app.entities.cart import CartPayment
from app.entities.coupon import CouponResponse
from app.entities.product import ProductSoldOutError
from app.infra.bootstrap.task_bootstrap import bootstrap, Command
from app.infra.constants import OrderStatus, PaymentMethod
from app.infra.payment_gateway.stripe_gateway import (
    PaymentGatewayRequestError,
)
from app.infra.worker import task_message_bus
from app.inventory.tasks import decrease_inventory
from app.order.entities import (
    CreateOrderStatusStepError,
    OrderDBUpdate,
    OrderNotFound,
)
from app.order.tasks import (
    create_order,
    create_order_status_step,
    update_order,
)
from app.payment.entities import CreatePaymentError, PaymentAcceptError
from app.payment.tasks import create_pending_payment, update_payment

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
    logger.info('Start checkout task')
    _ = payment_method
    order_id = None
    gateway_payment_id = None
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
        cart.discount = Decimal(0)
        affiliate_id = None
        coupon = cart.coupon if cart.coupon else None
        if coupon:
            coupon = await bootstrap.cart_uow.get_coupon_by_code(
                coupon,
                bootstrap=bootstrap,
            )
            affiliate_id = coupon.affiliate_id
        products_db = await bootstrap.cart_uow.get_products(
            products=cart.cart_items,
            bootstrap=bootstrap,
        )
        cart.get_products_price_and_discounts(products_db)
        products_inventory = await bootstrap.cart_uow.get_products_quantity(
            cart.cart_items,
            bootstrap=bootstrap,
        )
        products_in_cart = []
        products_in_inventory = []
        cart_quantities = []
        for product in products_db:
            logger.info(cart)
            logger.info(type(cart))
            for cart_item in cart.cart_items:
                products_in_cart.append(product.product_id)
                if any(
                    item['product_id'] == product.product_id
                    for item in products_inventory
                ):
                    products_in_inventory.append(product.product_id)
                for item in products_inventory:
                    if (
                        cart_item.product_id == item['product_id']
                        and cart_item.quantity > item['quantity']
                    ):
                        cart_quantities.append(cart_item.model_dump())

        products_not_in_both = list(
            set(products_in_cart) ^ set(products_in_inventory),
        )

        if cart_quantities:
            raise ProductSoldOutError(
                f'Os seguintes items solicitados estão com um pedido acima dos nossos estoques {cart_quantities}',
            )
        if len(products_db) != len(products_inventory):
            raise ProductSoldOutError(
                f'Os seguintes produtos não possuem em estoque {products_not_in_both}',
            )
        cart.get_products_price_and_discounts(products_db)
        zipcode = cart.zipcode
        no_spaces = zipcode.replace(' ', '')
        no_special_chars = re.sub(r'[^a-zA-Z0-9]', '', no_spaces)
        cart.zipcode = no_special_chars
        freight_package = bootstrap.freight.calculate_volume_weight(
            products=products_db,
        )
        if not cart.freight_product_code:
            raise HTTPException(
                status_code=400,
                detail='Freight product code not found',
            )
        freight = bootstrap.freight.get_freight(
            cart.freight_product_code,
            freight_package=freight_package,
            zipcode=cart.zipcode,
        )
        cart.freight = freight
        cart.calculate_subtotal(
            discount=coupon.discount if cart.coupon else 0,
        )
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
                    affiliate_id=affiliate_id,
                    coupon=coupon,
                    user=user,
                    payment_gateway=cart.gateway_provider,
                    gateway_payment_id=payment_response.id,
                    authorization=payment_response.authorization_code,
                    bootstrap=bootstrap,
                )
                gateway_payment_id = payment_response.authorization_code
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
                    if all([order_id, affiliate_id, coupon]):
                        await bootstrap.message.broker.publish(
                            {
                                'user_id': affiliate_id,
                                'order_id': order_id,
                                'commission_percentage': coupon.commission_percentage,
                                'coupon_id': coupon.coupon_id,
                                'subtotal': cart.subtotal,
                            },
                            queue=RabbitQueue('sales_commission'),
                        )
                    await bootstrap.message.broker.publish(
                        {
                            'mail_to': user.email,
                            'order_id': order_id if order_id else '',
                        },
                        queue=RabbitQueue('notification_order_paid'),
                    )
                logger.info(
                    f'Checkout cart {cart_uuid} with payment {payment_id} processed with success',
                )
                bootstrap.cache.delete(cart_uuid)
            case (PaymentMethod.PIX.value):
                logger.info('Start pix payment')
                payment_id, order_id = await create_pending_payment_and_order(
                    cart=cart,
                    affiliate_id=affiliate_id,
                    coupon=coupon,
                    payment_gateway=cart.gateway_provider,
                    user=user,
                    gateway_payment_id=cart.pix_payment_id,
                    bootstrap=bootstrap,
                )
                gateway_payment_id = cart.pix_payment_id
                logger.info(
                    f'Checkout cart {cart_uuid} with payment {payment_id} concluded with success',
                )
                bootstrap.cache.set(cart_uuid, 18000)
            case (_):
                raise Exception('Payment method not found')

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
    return {
        'order_id': {order_id},
        'gateway_payment_id': gateway_payment_id,
        'message': 'processed',
        'qr_code': getattr(cart, 'pix_qr_code', None),
        'qr_code_base64': getattr(cart, 'pix_qr_code_base64', None),
    }


async def create_pending_payment_and_order(
    cart: CartPayment,
    affiliate_id: int | None,
    coupon: CouponResponse | None,
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
            affiliate_id=affiliate_id,
            coupon=coupon,
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
