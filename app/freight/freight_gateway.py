from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Self

from pydantic import BaseModel


class FreightCart(BaseModel):
    """Freight cart."""

    volume: float
    weight: float


class AbstractFreight(ABC):
    """Abstract class to implement a freight gateway."""

    async def calculate_volume_weight(
        self: Self,
        zipcode: str,
        *,
        products: list,
    ) -> FreightCart:
        """Calculate volume and weight from cart."""
        return await self._calculate_volume_weight(zipcode, products=products)

    async def get_freight(
        self: Self,
        zipcode: str,
        *,
        volume: float,
        weight: float,
    ) -> Decimal:
        """Get freight from zip code."""
        return await self._get_freight(zipcode, volume=volume, weight=weight)

    @abstractmethod
    async def _calculate_volume_weight(
        self: Self,
        zipcode: str,
        *,
        products: list,
    ) -> FreightCart:
        """Calculate volume and weight from cart."""
        ...

    @abstractmethod
    async def _get_freight(
        self: Self,
        zipcode: str,
        *,
        volume: float,
        weight: float,
    ) -> Decimal:
        """Get freight from zip code."""
        ...


class MemoryFreight(AbstractFreight):
    """Memory implementation of freight gateway."""

    async def _calculate_volume_weight(
        self: Self,
        zipcode: str,
        *,
        products: list,
    ) -> FreightCart:
        """Calculate volume and weight from cart."""
        _ = products, zipcode
        return FreightCart(
            volume=0.0,
            weight=0.0,
        )

    async def _get_freight(
        self: Self,
        zipcode: str,
        *,
        volume: float,
        weight: float,
    ) -> Decimal:
        """Get freight from zip code."""
        _ = volume, weight, zipcode
        return Decimal('10.0')
