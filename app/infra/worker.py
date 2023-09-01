from propan.fastapi import RabbitRouter
from propan.brokers.rabbit.rabbit_broker import RabbitBroker as RabbitMQBroker
from config import settings
from pydantic import BaseModel

task_cart_router = RabbitRouter(settings.BROKER_URL)
task_payment_router = RabbitRouter(settings.BROKER_URL)
task_order_router = RabbitRouter(settings.BROKER_URL)
task_inventory_router = RabbitRouter(settings.BROKER_URL)
task_mail_router = RabbitRouter(settings.BROKER_URL)


class Broker(BaseModel):
    cart: RabbitMQBroker
    payment: RabbitMQBroker
    order: RabbitMQBroker
    inventory: RabbitMQBroker
    mail: RabbitMQBroker

    class Config:
        arbitrary_types_allowed = True


mq_broker = Broker(
    cart=task_cart_router.broker,
    payment=task_payment_router.broker,
    order=task_order_router.broker,
    inventory=task_inventory_router.broker,
    mail=task_mail_router.broker,
)

memory_broker = Broker(
    cart=task_cart_router.broker,
    payment=task_payment_router.broker,
    order=task_order_router.broker,
    inventory=task_inventory_router.broker,
    mail=task_mail_router.broker,
)
