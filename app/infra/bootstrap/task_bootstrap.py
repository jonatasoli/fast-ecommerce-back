from propan.fastapi import RabbitRouter
from app.infra.worker import task_message_bus
from pydantic import BaseModel

import redis as cache_client
from sqlalchemy.orm import Session, sessionmaker
from app.infra import stripe
from app.cart.repository import SqlAlchemyRepository
from app.order import repository as order_repository
from app.inventory import repository as inventory_repository
from app.payment import repository as payment_repository
from app.user import repository as user_repository
from app.infra import redis
from app.freight import freight_gateway as freight
from app.cart.uow import get_session
from app.user import gateway as user_gateway
from typing import Any


class Command(BaseModel):
    """Command to use in the application."""

    db: sessionmaker
    cart_repository: Any
    inventory_repository: Any
    payment_repository: Any
    user_repository: Any
    cache: redis.MemoryClient | cache_client.Redis
    message: RabbitRouter
    freight: freight.AbstractFreight
    user: Any
    payment: Any

    class Config:
        """Pydantic configs."""

        arbitrary_types_allowed = True


async def bootstrap(  # noqa: PLR0913
    db: sessionmaker = get_session(),
    cart_repository: Any = SqlAlchemyRepository,
    inventory_repository: Any = inventory_repository.SqlAlchemyRepository,
    payment_repository: Any = payment_repository.SqlAlchemyRepository,
    user_repository: Any = user_repository.SqlAlchemyRepository,
    cache: redis.AbstractCache = redis.RedisCache(),
    message: RabbitRouter = task_message_bus,
    freight: freight.AbstractFreight = freight.MemoryFreight(),
    user: Any = user_gateway,  # noqa: ANN401
    payment: Any = stripe,  # noqa: ANN401
) -> Command:
    """Create a command function to use in the application."""
    _cache = cache.client()
    _user = user

    _cart_repository = cart_repository(db().begin())
    _inventory_repository = inventory_repository(db().begin())
    _payment_repository = payment_repository(db().begin())
    _user_repository = user_repository(db().begin())

    return Command(
        db=db,
        cart_repository=_cart_repository,
        inventory_repository=_inventory_repository,
        payment_repository=_payment_repository,
        user_repository=_user_repository,
        cache=_cache,
        message=message,
        freight=freight,
        user=_user,
        payment=payment,
    )
