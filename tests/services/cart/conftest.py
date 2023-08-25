import pytest
from app.cart.uow import MemoryUnitOfWork

from app.infra.bootstrap.cart_bootstrap import Command, bootstrap
from app.infra.queue import MemoryPublish
from app.infra.redis import MemoryCache


@pytest.fixture(name='memory_bootstrap')
async def memory_bootstrap() -> Command:
    return await bootstrap(
        uow=MemoryUnitOfWork(),
        cache=MemoryCache(),
        broker=MemoryPublish(),
    )
