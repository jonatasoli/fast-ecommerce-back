from app.infra.worker import Broker, mq_broker
from pydantic import BaseModel

import redis as cache_client
from sqlalchemy.orm import Session, sessionmaker
from app.infra import stripe
from app.cart.repository import AbstractRepository, SqlAlchemyRepository
from app.order import repository as order_repository
from app.infra import redis
from app.freight import freight_gateway as freight
from app.cart.uow import get_session
from app.user import gateway as user_gateway
from typing import Any


class Command(BaseModel):
    """Command to use in the application."""

    db: sessionmaker
    cart_repository: Any
    order_repository: Any
    cache: redis.MemoryClient | cache_client.Redis
    broker: Broker
    freight: freight.AbstractFreight
    user: Any
    payment: Any

    class Config:
        """Pydantic configs."""

        arbitrary_types_allowed = True


async def bootstrap(  # noqa: PLR0913
    db: Session = get_session(),
    cart_repository: Any = SqlAlchemyRepository,
    order_repository: Any = order_repository.SqlAlchemyRepository,
    cache: redis.AbstractCache = redis.RedisCache(),
    broker: Broker = mq_broker,
    freight: freight.AbstractFreight = freight.MemoryFreight(),
    user: Any = user_gateway,  # noqa: ANN401
    payment: Any = stripe,  # noqa: ANN401
) -> Command:
    """Create a command function to use in the application."""
    _cache = cache.client()
    _user = user

    return Command(
        db=db,
        cart_repository=cart_repository,
        order_repository=order_repository,
        cache=_cache,
        broker=broker,
        freight=freight,
        user=_user,
        payment=payment,
    )
