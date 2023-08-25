from abc import ABC, abstractmethod
from decimal import Decimal
from typing import TypeVar

from pydantic import BaseModel


Self = TypeVar('Self')


class FreightCart(BaseModel):
    """Freight cart."""

    volume: float
    weight: float


class AbstractFreight(ABC):
    """Abstract class to implement a freight gateway."""

    async def calculate_volume_weight(
        self: Self,
        products: list,
    ) -> FreightCart:
        """Calculate volume and weight from cart."""
        return await self._calculate_volume_weight(products)

    async def get_freight(
        self: Self,
        volume: float,
        weight: float,
        zipcode: str,
    ) -> Decimal:
        """Get freight from zip code."""
        return await self._get_freight(volume, weight, zipcode)

    @abstractmethod
    async def _calculate_volume_weight(
        self: Self,
        products: list,
    ) -> FreightCart:
        """Calculate volume and weight from cart."""
        ...

    @abstractmethod
    async def _get_freight(
        self: Self,
        volume: float,
        weight: float,
        zipcode: str,
    ) -> Decimal:
        """Get freight from zip code."""
        ...


class MemoryFreight(AbstractFreight):
    """Memory implementation of freight gateway."""

    async def _calculate_volume_weight(
        self: Self,
        products: list,
    ) -> FreightCart:
        """Calculate volume and weight from cart."""
        _ = products
        return FreightCart(
            volume=0.0,
            weight=0.0,
        )

    async def _get_freight(
        self: Self,
        freight_cart: FreightCart,
        zipcode: str,
    ) -> Decimal:
        """Get freight from zip code."""
        _ = freight_cart, zipcode
        return Decimal('10.0')
