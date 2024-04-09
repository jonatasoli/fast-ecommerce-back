from pydantic import BaseModel, ConfigDict

from pydantic.dataclasses import dataclass
import redis as cache_client
from sqlalchemy.orm import sessionmaker
from app.infra import redis
from app.infra.database import get_async_session as get_session
from typing import Any
from app.user import uow as user_uow


class Command(BaseModel):
    """Command to use in the application."""

    db: sessionmaker
    user_uow: Any
    cache: redis.MemoryClient | cache_client.Redis

    model_config = ConfigDict(arbitrary_types_allowed=True)



async def bootstrap(
    db: sessionmaker = get_session(),
    user_uow: Any = user_uow,
    cache: redis.AbstractCache = redis.RedisCache(),
) -> Command:
    """Create a command function to use in the application."""
    _cache = cache.client()

    return Command(
        db=db,
        user_uow=user_uow,
        cache=_cache,
    )
