from faststream.rabbit.fastapi import RabbitRouter

from pydantic import BaseModel, ConfigDict

from pydantic.dataclasses import dataclass
import redis as cache_client
from sqlalchemy.orm import sessionmaker
from app.payment import repository as payment_repository
from app.user import repository as user_repository
from app.infra.database import get_async_session as get_session
from app.infra import redis
from typing import Any
from app.infra.worker import task_message_bus
from app.infra.payment_gateway import payment_gateway


class Command(BaseModel):
    """Command to use in the application."""

    db: Any
    cache: redis.MemoryClient | cache_client.Redis
    message: RabbitRouter
    payment_repository: Any
    user_repository: Any
    payment: Any

    model_config = ConfigDict(arbitrary_types_allowed=True)


async def bootstrap(
    db=get_session(),
    cache: redis.AbstractCache = redis.RedisCache(),
    message: RabbitRouter = task_message_bus,
    payment_repository: Any = payment_repository,  # noqa: ANN401
    user_repository: Any = user_repository,  # noqa: ANN401
    payment: Any = payment_gateway,  # noqa: ANN401
) -> Command:
    """Create a command function to use in the application."""
    _cache = cache.client()

    return Command(
        db=db,
        cache=_cache,
        message=message,
        payment_repository=payment_repository,
        user_repository=user_repository,
        payment=payment,
    )
