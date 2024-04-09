from typing import Any
from pydantic import BaseModel, ConfigDict
import pytest
from app.cart.uow import MemoryUnitOfWork
from app.cart import repository as cart_repository

from app.infra.redis import MemoryCache


class Command(BaseModel):
    """Command to use in the application."""

    db: Any
    uow: Any
    cart_uow: Any
    cart_repository: Any
    cache: Any
    message: Any
    freight: Any
    user: Any
    payment: Any

    model_config = ConfigDict(arbitrary_types_allowed=True)



async def bootstrap(  # noqa: PLR0913
    db: Any,
    uow: Any = None,
    cart_uow: Any = None,
    cart_repository: Any = None,
    cache: Any = None,
    message: Any = None,
    freight: Any = None,
    user: Any = None,
    payment: Any = None,  # noqa: ANN401
) -> Command:
    """Create a command function to use in the application."""
    return Command(
        db=db,
        uow=uow,
        cart_uow=cart_uow,
        cart_repository=cart_repository,
        cache=cache,
        message=message,
        freight=freight,
        user=user,
        payment=payment,
    )


@pytest.fixture(name='memory_bootstrap')
async def memory_bootstrap(mocker) -> Command:
    mock = mocker.Mock()
    return await bootstrap(
        db=mock,
        uow=MemoryUnitOfWork(),
        cart_repository=cart_repository,
        cart_uow=mock,
        cache=MemoryCache(),
        message=mock,
        freight=mock,
        user=mock,
        payment=mock,
    )
