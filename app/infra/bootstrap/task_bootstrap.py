from fastapi import Depends
from pydantic import BaseModel

import redis as cache_client
from sqlalchemy.orm import Session, sessionmaker
from app.infra import stripe
from app.cart import uow
from app.cart.repository import AbstractRepository, SqlAlchemyRepository
from app.infra import redis
from app.freight import freight_gateway as freight
from app.infra.sync_session import get_session
from app.user import gateway as user_gateway
from typing import Any


class Command(BaseModel):
    """Command to use in the application."""

    db: sessionmaker
    cart_repository: AbstractRepository
    cache: redis.MemoryClient | cache_client.Redis
    publish: Any
    freight: freight.AbstractFreight
    user: Any
    payment: Any

    class Config:
        """Pydantic configs."""

        arbitrary_types_allowed = True


def bootstrap(  # noqa: PLR0913
    db: Session = get_session(),
    cart_repository: AbstractRepository = Depends(SqlAlchemyRepository),
    cache: redis.AbstractCache = redis.RedisCache(),  # noqa: B008
    publish: Any = None,  # noqa: ANN401
    freight: freight.AbstractFreight = freight.MemoryFreight(),  # noqa: B008
    user: Any = user_gateway,  # noqa: ANN401
    payment: Any = stripe,  # noqa: ANN401
) -> Command:
    """Create a command function to use in the application."""
    _cache = cache.client()
    _user = user

    return Command(
        db=db,
        cart_repository=cart_repository,
        cache=_cache,
        publish=publish,
        freight=freight,
        user=_user,
        payment=payment,
    )
