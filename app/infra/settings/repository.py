from functools import lru_cache

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import SessionTransaction

from app.infra import models

class SettingNotFoundError(Exception):
    ...

@lru_cache
async def get_settings(
    field: str,
    transaction: AsyncSession,
) -> models.SettingsDB:
    """Must return a coupon by code."""
    async with transaction as session:
        setting = await session.execute(
            select(models.SettingsDB).where(
                models.SettingsDB.field == field,
            ),
        )
        if not setting:
            raise SettingNotFoundError

        return setting.scalar_one()
