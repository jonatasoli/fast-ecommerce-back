from collections import abc
from typing import TypeVar


# TODO: implementar entity
class Coupon:
    ...


Self = TypeVar('Self')

# Abstração da classe de repositório
class AbstractRepository(abc.ABC):
    """Abstract coupon repository."""

    def __init__(self: Self) -> None:
        self.seen = set()  # type: Set[Coupon]

    def add(self: Self, coupon: Coupon) -> Coupon:
        self._add(coupon)
        self.seen.add(coupon)

    def get(self: Self, coupon_name: str) -> Coupon:
        coupon = self._get(coupon_name)
        if coupon:
            self.seen.add(coupon)
        return coupon

    @abc.abstractmethod
    def _add(self: Self, coupon: Coupon) -> Coupon:
        raise NotImplementedError

    @abc.abstractmethod
    def _get(self: Self, coupon_name: str) -> Coupon:
        raise NotImplementedError


# Aqui temos a implementação do sqlalchemy executando as queries
# class SqlAlchemyRepository(AbstractRepository):
#     ...
