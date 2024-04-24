from taskiq_faststream import StreamScheduler
from loguru import logger
from taskiq.schedule_sources import LabelScheduleSource
from taskiq_faststream import BrokerWrapper
from faststream.rabbit import RabbitBroker
from app.cart import services as cart

DEFAULT_TTL=172800

broker = RabbitBroker("amqp://guest:guest@localhost:5672//")

taskiq_broker = BrokerWrapper(broker)
taskiq_broker.task(
    queue="in-queue",
    schedule=[{
        "cron": "*/1 * * * *",
        # "cron": "0 */12 * * *",
    }],
    )


scheduler = StreamScheduler(
    broker=taskiq_broker,
    sources=[LabelScheduleSource(taskiq_broker)],
)

@broker.subscriber("in-queue")
@broker.publisher("out-queue")
async def get_abandoned_carts() -> str:
    """Task to get all carts abandoned in redis."""
    logger.info("Start cart task")
    await cart.get_cart_and_send_to_crm()
    logger.info("Finish cart task")
    return "Task: registered"

