from propan.fastapi import RabbitRouter
from pydantic import BaseModel

import redis as cache_client
from sqlalchemy.orm import sessionmaker
from app.payment import repository as payment_repository
from app.infra.database import get_async_session as get_session
from app.infra import redis
from typing import Any
from app.infra.worker import task_message_bus


class Command(BaseModel):
    """Command to use in the application."""

    db: sessionmaker
    cache: redis.MemoryClient | cache_client.Redis
    message: RabbitRouter
    payment_repository: Any

    class Config:
        """Pydantic configs."""

        arbitrary_types_allowed = True


async def bootstrap(
    db: sessionmaker = get_session(),
    cache: redis.AbstractCache = redis.RedisCache(),
    message: RabbitRouter = task_message_bus,
    payment: Any = payment_repository,  # noqa: ANN401
) -> Command:
    """Create a command function to use in the application."""
    _cache = cache.client()

    return Command(
        db=db,
        cache=_cache,
        message=message,
        payment_repository=payment,
    )
