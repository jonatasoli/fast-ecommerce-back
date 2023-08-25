from propan.fastapi import RabbitRouter
from config import settings
from pydantic import BaseModel

task_cart_router = RabbitRouter(settings.BROKER_URL)
task_payment_router = RabbitRouter(settings.BROKER_URL)
task_order_router = RabbitRouter(settings.BROKER_URL)
task_inventory_router = RabbitRouter(settings.BROKER_URL)
task_mail_router = RabbitRouter(settings.BROKER_URL)


class Broker(BaseModel):
    cart: RabbitRouter
    payment: RabbitRouter
    order: RabbitRouter
    inventory: RabbitRouter
    mail: RabbitRouter


broker = Broker(
    cart=task_cart_router.broker,
    payment=task_payment_router.broker,
    order=task_order_router.broker,
    inventory=task_inventory_router.broker,
    mail=task_mail_router.broker,
)
