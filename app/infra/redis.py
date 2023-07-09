import abc
from typing import TypeVar
from typing import ClassVar


Self = TypeVar('Self')


class AbstractCache(abc.ABC):   # noqa: B024
    ...


class RedisCache(AbstractCache):
    ...


class MemoryCache(AbstractCache):
    cache: ClassVar[dict] = {}

    def set(self: Self, key: str, value: str) -> dict:   # noqa: A003
        self.cache[key] = value
        return self.cache

    def get(self: Self, key: str) -> dict:
        return self.cache.get(key)
