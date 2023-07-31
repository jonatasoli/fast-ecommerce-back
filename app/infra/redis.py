import abc
from typing import TypeVar
from typing import ClassVar
from config import settings
import redis


Self = TypeVar('Self')


class AbstractCache(abc.ABC):
    def client(self: Self) -> redis.Redis:
        return self._client()

    @abc.abstractmethod
    def _client(self: Self) -> redis.Redis:
        raise NotImplementedError


class RedisCache(AbstractCache):
    def __init__(self: Self) -> None:
        self.pool = redis.ConnectionPool(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
        )
        self.redis = redis.Redis(connection_pool=self.pool)

    def _client(self: Self) -> redis.Redis:
        return self.redis


class MemoryClient:
    cache: ClassVar[dict] = {}

    def set(self: Self, key: str, value: str) -> dict:   # noqa: A003
        self.cache[key] = value
        return self.cache

    def get(self: Self, key: str) -> dict:
        return self.cache.get(key)


class MemoryCache(AbstractCache):
    def __init__(self: Self) -> None:
        self.client_instance = MemoryClient()

    def _client(self: Self) -> MemoryClient:
        return self.client_instance
