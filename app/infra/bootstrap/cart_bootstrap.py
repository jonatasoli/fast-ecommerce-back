from pydantic import BaseModel

import redis as cache_client
from app.infra import stripe
from app.cart import uow
from app.cart.uow import SqlAlchemyUnitOfWork
from app.infra import redis
from app.freight import freight_gateway as freight
from app.user import gateway as user_gateway
from typing import Any
from app.infra.worker import task_cart_router


class Command(BaseModel):
    """Command to use in the application."""

    uow: uow.AbstractUnitOfWork
    cache: redis.MemoryClient | cache_client.Redis
    publish: Any
    freight: freight.AbstractFreight
    user: Any
    payment: Any

    class Config:
        """Pydantic configs."""

        arbitrary_types_allowed = True


async def bootstrap(  # noqa: PLR0913
    uow: uow.AbstractUnitOfWork = None,
    cache: redis.AbstractCache = redis.RedisCache(),  # noqa: B008
    publish: Any = task_cart_router.broker,  # noqa: ANN401
    freight: freight.AbstractFreight = freight.MemoryFreight(),  # noqa: B008
    user: Any = user_gateway,  # noqa: ANN401
    payment: Any = stripe,  # noqa: ANN401
) -> Command:
    """Create a command function to use in the application."""
    if uow is None:
        uow = SqlAlchemyUnitOfWork()

    _cache = cache.client()
    _user = user

    return Command(
        uow=uow,
        cache=_cache,
        publish=publish,
        freight=freight,
        user=_user,
        payment=payment,
    )
