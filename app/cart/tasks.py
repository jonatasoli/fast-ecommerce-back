import asyncio
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Self

from fastapi import Depends
from app.infra.database import get_async_session, get_session
from loguru import logger
from faststream.rabbit import RabbitQueue
from app.cart.services import calculate_freight, consistency_inventory

from app.entities.cart import CartPayment
from app.entities.coupon import CouponInDB
from app.infra.bootstrap.task_bootstrap import bootstrap, Command
from app.infra.constants import OrderStatus, PaymentGatewayAvailable, PaymentMethod
from app.infra.payment_gateway.stripe_gateway import (
    PaymentGatewayRequestError,
)
from app.infra.worker import task_message_bus
from app.inventory.tasks import decrease_inventory
from app.entities.order import (
    CreateOrderStatusStepError,
    OrderDBUpdate,
    OrderNotFoundError,
)
from app.order.tasks import (
    create_order,
    create_order_status_step,
    update_order,
)
from app.entities.payment import CreatePaymentError, PaymentAcceptError
from app.payment.tasks import create_pending_payment, update_payment
from app.cart.retry import get_backoff_delay

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


@task_message_bus.subscriber('checkout')
async def checkout(  # noqa: C901, PLR0913
    cart_uuid: str,
    payment_method: str,
    payment_gateway: str,
    user: Any,
    bootstrap: Any = Depends(get_bootstrap),
    db=Depends(get_session),
    async_db=Depends(get_async_session),
) -> dict:
    """Checkout cart with payment intent."""
    logger.info('Start checkout task')
    _ = payment_method
    order_id = None
    gateway_payment_id = None
    logger.info(
        f'Checkout cart start{cart_uuid} with gateway {payment_gateway} with success',
    )
    now = datetime.now(timezone.utc)
    try:
        cache = bootstrap.cache
        cache_cart = cache.get(cart_uuid)
        if not cache_cart:
            job = await bootstrap.cart_repository.get_checkout_job(
                cart_uuid=cart_uuid,
                transaction=bootstrap.db,
            )
            if job and job.payload:
                logger.warning(
                    'Cart não encontrado no cache, usando payload do job '
                    '(cart_uuid=%s)',
                    cart_uuid,
                )
                cart = CartPayment.model_validate(**job.payload)
            else:
                msg = (
                    f'Cart not found in cache and no job payload '
                    f'(cart_uuid={cart_uuid})'
                )
                logger.error(msg)
                raise RuntimeError(msg)
        else:
            cart = CartPayment.model_validate_json(cache_cart)
        cart.discount = Decimal(0)
        job = await bootstrap.cart_repository.get_checkout_job(
            cart_uuid=cart_uuid,
            transaction=bootstrap.db,
        )
        if job and job.status == 'succeeded':
            logger.info(
                f'Checkout job já concluído (cart_uuid={cart_uuid}), pulando reprocessamento.',
            )
            return {
                'order_id': job.order_id or '',
                'gateway_payment_id': job.gateway_payment_id,
                'message': 'processed',
                'qr_code': getattr(cart, 'pix_qr_code', None),
                'qr_code_base64': getattr(cart, 'pix_qr_code_base64', None),
            }
        if job and job.next_run_at and job.next_run_at > now:
            logger.info(
                f'Checkout job scheduled for later (next_run_at={job.next_run_at}), skipping execution now.',
            )
            return {}
        current_attempts = job.attempts if job else 0
        await bootstrap.cart_repository.upsert_checkout_job(
            cart_uuid=cart_uuid,
            payment_gateway=payment_gateway,
            payment_method=payment_method,
            payload=cart.model_dump(),
            status='processing',
            attempts=current_attempts,
            next_run_at=None,
            last_run_at=now,
            last_error=None,
            order_id=job.order_id if job else None,
            gateway_payment_id=job.gateway_payment_id if job else None,
            transaction=bootstrap.db,
        )
        affiliate_id = None
        coupon = cart.coupon if cart.coupon else None
        if coupon != 'null' and coupon:
            coupon = await bootstrap.cart_uow.get_coupon_by_code(
                coupon,
                bootstrap=bootstrap,
            )
            affiliate_id = coupon.affiliate_id
        else:
            coupon = None
            cart.coupon = None
        product_ids: list[int] = [item.product_id for item in cart.cart_items]
        products_db = await bootstrap.cart_repository.get_products_quantity(
            products=product_ids,
            transaction=bootstrap.db().begin(),
        )
        consistency_inventory(
            cart,
            products_inventory=products_db,
        )
        cart.get_products_price_and_discounts(products_db)
        logger.debug(f'checkout: após get_products_price_and_discounts, itens={[(item.product_id, item.price, item.quantity) for item in cart.cart_items]}')
        cart = await calculate_freight(
            cart=cart,
            products_db=products_db,
            bootstrap=bootstrap,
            session=async_db,
        )
        cart.calculate_subtotal(
            coupon=coupon if cart.coupon else None,
        )
        logger.debug(f'checkout: após calculate_subtotal, subtotal={cart.subtotal}, total={cart.total}')
        match cart.payment_method:
            case PaymentMethod.CREDIT_CARD.value:
                logger.info(
                    '💳 Processando pagamento com cartão de crédito | '
                    'Gateway: %s | Valor: R$ %s | Parcelas: %s',
                    cart.gateway_provider,
                    cart.total,
                    cart.installments,
                )
                payment_response = bootstrap.payment.create_credit_card_payment(
                    payment_gateway=cart.gateway_provider,
                    customer_id=cart.customer_id,
                    amount=cart.total,
                    card_token=cart.card_token,
                    installments=cart.installments,
                    customer_email=user['email'],
                    payment_intent_id=cart.payment_intent,
                    payment_method=cart.payment_method_id,
                )
                authorization_code = None
                if payment_method == PaymentGatewayAvailable.STRIPE.value:
                    authorization_code = payment_response.payment_method
                elif payment_method == PaymentGatewayAvailable.MERCADOPAGO.value:
                    authorization_code = payment_response.get('id')
                else:
                    authorization_code = 'invalid'

                payment_id, order_id = await create_pending_payment_and_order(
                    cart=cart,
                    affiliate_id=affiliate_id,
                    coupon=coupon,
                    user=user,
                    payment_gateway=cart.gateway_provider,
                    gateway_payment_id=payment_response.id,
                    authorization=authorization_code,
                    bootstrap=bootstrap,
                )
                _payment_id = payment_id
                gateway_payment_id = authorization_code
                logger.info(
                    '✅ Pagamento processado | Payment ID: %s | Order ID: %s | Status: %s',
                    payment_response.id,
                    order_id,
                    getattr(payment_response, 'status', 'unknown'),
                )
                logger.debug(f'PAyment Response {payment_response}')
                cart.payment_intent = payment_response.id
                logger.debug(f'Payment Intent {cart.payment_intent}')
                authorization = authorization_code
                payment_accept = None
                if payment_response.status not in ['in_process', 'rejected']:
                    logger.info('🔄 Aceitando pagamento no gateway...')
                    payment_accept = bootstrap.payment.accept_payment(
                        payment_gateway=cart.gateway_provider,
                        payment_id=cart.payment_intent,
                    )
                    logger.info(
                        '✅ Pagamento aceito no gateway | Status: %s',
                        getattr(payment_accept, 'status', 'unknown'),
                    )
                    logger.debug(f'Payment response: {payment_accept}')

                await decrease_inventory(
                    cart=cart,
                    order_id=order_id,
                    bootstrap=bootstrap,
                )
                payment_accept_status = getattr(
                    payment_accept,
                    'status',
                    'PENDING',
                )
                if payment_accept_status == 'approved':
                    logger.info(
                        '✅✅ Pagamento APROVADO | Order ID: %s | Payment ID: %s',
                        order_id,
                        payment_id,
                    )
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
                        payment_status=payment_accept_status,
                        processed=True,
                        bootstrap=bootstrap,
                    )
                    await create_order_status_step(
                        order_id=order_id,
                        status=OrderStatus.PAYMENT_PAID.value,
                        send_mail=True,
                        bootstrap=bootstrap,
                    )
                logger.debug('Debug comission credit card')
                logger.debug(f'Order Id {order_id}')
                logger.debug(f'Affiliate {affiliate_id}')
                logger.debug(f'subtotal {cart.subtotal}')
                logger.debug(f'Coupon {coupon}')
                logger.debug(f'payment_Id {_payment_id}')
                if all([order_id, affiliate_id, coupon, _payment_id]):
                    logger.debug('Credit Card task start')
                    await bootstrap.message.broker.publish(
                        {
                            'user_id': affiliate_id,
                            'order_id': order_id,
                            'subtotal': cart.subtotal,
                            'coupon_id': coupon.coupon_id,
                            'commission_percentage': coupon.commission_percentage,
                            'payment_id': _payment_id,
                        },
                        queue=RabbitQueue('sales_commission'),
                    )
                else:
                    logger.debug('Not commission')
                await bootstrap.message.broker.publish(
                    {
                        'mail_to': user['email'],
                        'order_id': order_id if order_id else '',
                    },
                    queue=RabbitQueue('notification_order_paid'),
                )
                logger.info(
                    f'Checkout cart {cart_uuid} with payment {payment_id} processed with success',
                )
                bootstrap.cache.delete(cart_uuid)
            case PaymentMethod.PIX.value:
                logger.info(
                    '📱 Processando pagamento PIX | '
                    'Gateway: %s | Valor: R$ %s | Payment ID: %s',
                    cart.gateway_provider,
                    cart.total,
                    cart.pix_payment_id,
                )
                payment_id, order_id = await create_pending_payment_and_order(
                    cart=cart,
                    affiliate_id=affiliate_id,
                    coupon=coupon,
                    payment_gateway=cart.gateway_provider,
                    user=user,
                    gateway_payment_id=cart.pix_payment_id,
                    bootstrap=bootstrap,
                    pix=True,
                )
                gateway_payment_id = cart.pix_payment_id
                logger.info(
                    '✅ Pagamento PIX processado | Payment ID: %s | Order ID: %s',
                    payment_id,
                    order_id,
                )
                logger.info(
                    f'Checkout cart {cart_uuid} with payment {payment_id} concluded with success',
                )
                bootstrap.cache.set(
                    cart_uuid,
                    cart.model_dump_json(),
                    ex=18000,
                )
                logger.debug('Debug comission Pix')
                logger.debug(f'Order Id {order_id}')
                logger.debug(f'Affiliate {affiliate_id}')
                logger.debug(f'subtotal {cart.subtotal}')
                logger.debug(f'Coupon {coupon}')
                logger.debug(f'payment_Id {payment_id}')
                if all([order_id, affiliate_id, coupon, payment_id]):
                    await bootstrap.message.broker.publish(
                        {
                            'user_id': affiliate_id,
                            'order_id': order_id,
                            'subtotal': cart.subtotal,
                            'coupon_id': coupon.coupon_id,
                            'commission_percentage': coupon.commission_percentage,
                            'payment_id': payment_id,
                        },
                        queue=RabbitQueue('sales_commission'),
                    )
            case _:
                msg = 'Payment method not found'
                raise ValueError(msg)

        await bootstrap.cart_repository.upsert_checkout_job(
            cart_uuid=cart_uuid,
            payment_gateway=payment_gateway,
            payment_method=payment_method,
            payload=None,
            status='succeeded',
            attempts=current_attempts,
            next_run_at=None,
            last_run_at=now,
            last_error=None,
            order_id=str(order_id) if order_id else None,
            gateway_payment_id=str(gateway_payment_id) if gateway_payment_id else None,
            transaction=bootstrap.db,
        )
        await bootstrap.cart_repository.cleanup_checkout_jobs(
            transaction=bootstrap.db,
        )
    except (PaymentAcceptError, PaymentGatewayRequestError) as e:
        last_error = PAYMENT_STATUS_ERROR_MESSAGE if isinstance(
            e,
            PaymentAcceptError,
        ) else PAYMENT_REQUEST_ERROR_MESSAGE
        logger.error(f'Payment error in checkout: {last_error}')
        next_attempt = (current_attempts if "current_attempts" in locals() else 0) + 1
        delay = get_backoff_delay(current_attempts)
        status = 'failed' if delay is None else 'pending'
        next_run_at = now + timedelta(seconds=delay) if delay else None
        await bootstrap.cart_repository.upsert_checkout_job(
            cart_uuid=cart_uuid,
            payment_gateway=payment_gateway,
            payment_method=payment_method,
            payload=cart.model_dump() if 'cart' in locals() else None,
            status=status,
            attempts=next_attempt,
            next_run_at=next_run_at,
            last_run_at=now,
            last_error=last_error,
            order_id=str(order_id) if order_id else None,
            gateway_payment_id=str(gateway_payment_id) if gateway_payment_id else None,
            transaction=bootstrap.db,
        )
        if delay:
            await asyncio.sleep(delay)
            await bootstrap.message.broker.publish(
                {
                    'cart_uuid': cart_uuid,
                    'payment_gateway': payment_gateway,
                    'payment_method': payment_method,
                    'user': user,
                },
                queue=RabbitQueue('checkout'),
            )
        return PAYMENT_STATUS_ERROR_MESSAGE
    except Exception as e:
        logger.error(f'Error in checkout: {e}')
        current_attempts = locals().get('current_attempts', 0)
        next_attempt = current_attempts + 1
        delay = get_backoff_delay(current_attempts)
        status = 'failed' if delay is None else 'pending'
        next_run_at = now + timedelta(seconds=delay) if delay else None
        await bootstrap.cart_repository.upsert_checkout_job(
            cart_uuid=cart_uuid,
            payment_gateway=payment_gateway,
            payment_method=payment_method,
            payload=cart.model_dump() if 'cart' in locals() else None,
            status=status,
            attempts=next_attempt,
            next_run_at=next_run_at,
            last_run_at=now,
            last_error=str(e),
            order_id=str(order_id) if order_id else None,
            gateway_payment_id=str(gateway_payment_id) if gateway_payment_id else None,
            transaction=bootstrap.db,
        )
        if delay:
            await asyncio.sleep(delay)
            await bootstrap.message.broker.publish(
                {
                    'cart_uuid': cart_uuid,
                    'payment_gateway': payment_gateway,
                    'payment_method': payment_method,
                    'user': user,
                },
                queue=RabbitQueue('checkout'),
            )
        return {}
    return {
        'order_id': str(order_id) if order_id else '',
        'gateway_payment_id': gateway_payment_id,
        'message': 'processed',
        'qr_code': getattr(cart, 'pix_qr_code', None),
        'qr_code_base64': getattr(cart, 'pix_qr_code_base64', None),
    }


async def create_pending_payment_and_order(
    cart: CartPayment,
    affiliate_id: int | None,
    coupon: CouponInDB | None,
    user: Any,
    payment_gateway: str,
    gateway_payment_id: int | str,
    bootstrap: Any,
    authorization: str = 'PENDING',
    pix: bool = False,
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
            raise OrderNotFoundError(
                msg,
            )
        payment_id = await create_pending_payment(
            order_id=order_id,
            cart=cart,
            user_id=user['user_id'],
            authorization=authorization,
            payment_gateway=payment_gateway,
            gateway_payment_id=gateway_payment_id,
            pix=pix,
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
