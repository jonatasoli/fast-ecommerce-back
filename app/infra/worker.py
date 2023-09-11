from loguru import logger
from propan.fastapi import RabbitRouter
from config import settings

logger.info(f'{settings.BROKER_URL}')
task_message_bus = RabbitRouter(settings.BROKER_URL)
