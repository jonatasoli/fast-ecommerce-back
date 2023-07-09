from pydantic import BaseModel

from app.cart import uow
from app.infra import redis, queue


class Command(BaseModel):
    """Command to use in the application."""

    uow: uow.AbstractUnitOfWork
    cache: redis.AbstractCache
    publish: queue.AbstractPublish

    class Config:
        """Pydantic configs."""

        arbitrary_types_allowed = True


async def bootstrap(
    uow: uow.AbstractUnitOfWork = None,
    cache: redis.AbstractCache = redis.RedisCache(),  # noqa: B008
    publish: queue.AbstractPublish = queue.RabbitMQPublish(),  # noqa: B008
) -> Command:
    """Create a command function to use in the application."""
    if uow is None:
        uow = await uow.SqlAlchemyUnitOfWork()

    return Command(
        uow=uow,
        cache=cache,
        publish=publish,
    )
