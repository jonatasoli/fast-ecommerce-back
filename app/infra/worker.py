from propan.fastapi import RabbitRouter
from config import settings

task_message_bus = RabbitRouter(settings.BROKER_URL)
