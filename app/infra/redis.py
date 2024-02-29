import abc
from typing import ClassVar, Self

from pydantic.types import Json
from config import settings
import redis


class AbstractCache(abc.ABC):
    def client(self: Self) -> redis.Redis:
        return self._client()

    @abc.abstractmethod
    def _client(self: Self) -> redis.Redis:
        raise NotImplementedError


class RedisCache(AbstractCache):
    def __init__(self: Self) -> None:
        self.pool = redis.ConnectionPool.from_url(
            url=settings.REDIS_URL,
            db=settings.REDIS_DB,
        )
        self.redis = redis.Redis(connection_pool=self.pool)

    def _client(self: Self) -> redis.Redis:
        return self.redis


class MemoryClient:
    cache: ClassVar[dict[str, str]] = {}

    def set(self: Self, key: str, value: str, ex: int) -> dict[str, str]:
        _ = ex
        self.cache[key] = value
        return self.cache

    def get(self: Self, key: str) -> str | bytes | bytearray:
        return self.cache[key]

    def delete(self: Self, key: str) -> dict:
        del self.cache[key]
        return self.cache


class MemoryCache(AbstractCache):
    def __init__(self: Self) -> None:
        self.client_instance = MemoryClient()

    def _client(self: Self) -> MemoryClient:
        return self.client_instance
