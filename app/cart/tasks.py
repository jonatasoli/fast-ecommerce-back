# ruff:  noqa: D202 D205 T201 D212
from app.worker import celery
from uuid import uuid4


@celery.task
def checkout(cart_uuid: uuid4, payment_intent: str) -> None:
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
    _ = payment_intent
    _ = cart_uuid
    print('checkout')
