from propan.brokers.rabbit import RabbitQueue
from propan.fastapi import RabbitRouter
from config import settings

task_cart_router = RabbitRouter(settings.BROKER_URL)


@task_cart_router.event(RabbitQueue('checkout'))
async def checkout(cart_uuid: str, payment_intent: str) -> int:
    """
    - Get cart from redis
    - Set affiliate if exists
    - Set coupon if exists
    - Calculate cart
    - Accept Payment Intent
    - uow
        - Create order
        - Create payment
        - Create transaction
        - Create order_status_step
        - Decrease inventory
    - Send email
    - return order.
    """
    # cache = bootstrap.cache
    # cache_cart = cache.get(cart_uuid)
    # if not cache_cart:
    #     raise Exception('Cart not found')
    # cart = CartPayment.model_validate_json(cache_cart)
    # affiliate = cart.affiliate if cart.affiliate else None
    # coupon = cart.coupon if cart.coupon else None
    # with bootstrap.db() as session:
    #     coupon = bootstrap.cart_repository.get_coupon_by_code(session, coupon)

    _ = payment_intent
    _ = cart_uuid
    print('checkout')
    return 123
