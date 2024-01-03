import pytest
from app.cart.uow import MemoryUnitOfWork

from app.infra.bootstrap.cart_bootstrap import Command, bootstrap
from app.infra.redis import MemoryCache


@pytest.fixture(name='memory_bootstrap')
async def memory_bootstrap(mocker) -> Command:
    mock = mocker.Mock()
    return await bootstrap(
        db=mock,
        uow=MemoryUnitOfWork(),
        cart_uow=mock,
        cache=MemoryCache(),
        message=mock,
        freight=mock,
        user=mock,
        payment=mock,
    )
