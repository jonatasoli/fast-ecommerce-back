from propan.fastapi import RabbitRouter
from app.infra.worker import task_message_bus
from pydantic import BaseModel

import redis as cache_client
from sqlalchemy.orm import sessionmaker
from app.infra.payment_gateway import stripe
from app.infra import redis
from app.freight import freight_gateway as freight
from app.infra.database import get_async_session as get_session
from app.user import gateway as user_gateway
from typing import Any
from app.order import uow as order_uow
from app.user import uow as user_uow
from app.payment import uow as payment_uow
from app.inventory import uow as inventory_uow


class Command(BaseModel):
    """Command to use in the application."""

    db: sessionmaker
    order_uow: Any
    user_uow: Any
    payment_uow: Any
    inventory_uow: Any
    cache: redis.MemoryClient | cache_client.Redis
    message: RabbitRouter
    freight: Any
    user: Any
    payment: Any

    class Config:
        """Pydantic configs."""

        arbitrary_types_allowed = True


async def bootstrap(  # noqa: PLR0913
    db: sessionmaker = get_session(),
    order_uow: Any = order_uow,
    user_uow: Any = user_uow,
    payment_uow: Any = payment_uow,
    inventory_uow: Any = inventory_uow,
    cache: redis.AbstractCache = redis.RedisCache(),
    message: RabbitRouter = task_message_bus,
    freight: Any = freight,
    user: Any = user_gateway,  # noqa: ANN401
    payment: Any = stripe,  # noqa: ANN401
) -> Command:
    """Create a command function to use in the application."""
    _cache = cache.client()
    _user = user

    return Command(
        db=db,
        order_uow=order_uow,
        user_uow=user_uow,
        payment_uow=payment_uow,
        inventory_uow=inventory_uow,
        cache=_cache,
        message=message,
        freight=freight,
        user=_user,
        payment=payment,
    )
