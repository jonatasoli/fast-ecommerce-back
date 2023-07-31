from pydantic import BaseModel

import redis as cache_client
from app.cart import uow
from app.cart.uow import SqlAlchemyUnitOfWork
from app.infra import redis, queue
from app.freight import freight_gateway as freight


class Command(BaseModel):
    """Command to use in the application."""

    uow: uow.AbstractUnitOfWork
    cache: redis.MemoryClient | cache_client.Redis
    publish: queue.AbstractPublish
    freight: freight.AbstractFreight

    class Config:
        """Pydantic configs."""

        arbitrary_types_allowed = True


async def bootstrap(
    uow: uow.AbstractUnitOfWork = None,
    cache: redis.AbstractCache = redis.RedisCache(),  # noqa: B008
    publish: queue.AbstractPublish = queue.RabbitMQPublish(),  # noqa: B008
    freight: freight.AbstractFreight = freight.MemoryFreight(),  # noqa: B008
) -> Command:
    """Create a command function to use in the application."""
    if uow is None:
        uow = SqlAlchemyUnitOfWork()

    _cache = cache.client()

    return Command(
        uow=uow,
        cache=_cache,
        publish=publish,
        freight=freight,
    )
