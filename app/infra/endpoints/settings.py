import json
from typing import Annotated

from fastapi.exceptions import HTTPException
from app.entities.settings import (
    MainSettings,
    SettingsResponse,
    SettingsCreate,
    SettingsUpdate,
    SettingsListResponse,
)
from app.entities.user import UserNotAdminError, UserNotFoundError
from fastapi import APIRouter, Depends, Query, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.infra.database import get_async_session
from app.settings import repository
from app.settings.repository import obfuscate_settings_value
from app.user import services as domain_user
from app.user.services import verify_admin_async

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='access_token')

settings = APIRouter(
    prefix='/settings',
    tags=['settings'],
)


def _to_settings_response(setting_db) -> SettingsResponse:
    """Convert SettingsDB to SettingsResponse with obfuscation."""
    value = setting_db.value
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            value = {}

    obfuscated_value = obfuscate_settings_value(setting_db.field, value)

    return SettingsResponse(
        settings_id=setting_db.settings_id,
        locale=setting_db.locale,
        provider=setting_db.provider,
        field=setting_db.field,
        value=obfuscated_value,
        description=setting_db.description,
        is_active=setting_db.is_active,
        is_default=setting_db.is_default,
    )


@verify_admin_async()
@settings.get(
    '/',
    summary='List settings',
    description='List all settings with optional filters',
    status_code=status.HTTP_200_OK,
)
async def list_settings(  # noqa: PLR0913
    *,
    field: Annotated[str | None, Query(description='Filter by field type')] = None,
    locale: Annotated[str | None, Query(description='Filter by locale')] = None,
    is_active: Annotated[
        bool | None,
        Query(description='Filter by active status'),
    ] = None,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_async_session)],
) -> SettingsListResponse:
    """List settings."""
    _ = token
    async with db.begin() as transaction:
        settings_list, total = await repository.list_settings(
            field=field,
            locale=locale,
            is_active=is_active,
            transaction=transaction,
            offset=offset,
            limit=limit,
        )

        return SettingsListResponse(
            settings=[_to_settings_response(s) for s in settings_list],
            total=total,
        )


@verify_admin_async()
@settings.get(
    '/legacy',
    summary='Get settings (legacy)',
    description='get a settings for field and locale (legacy endpoint)',
    status_code=status.HTTP_200_OK,
)
async def get_settings_legacy(
    *,
    field: str,
    locale: str,
    token: Annotated[str, Depends(oauth2_scheme)],
    db=Depends(get_async_session),
):
    """Get Setting (legacy)."""
    _ = token
    async with db.begin() as transaction:
        return await repository.get_settings(
            locale=locale,
            field=field,
            transaction=transaction,
        )


@verify_admin_async()
@settings.patch(
    '/legacy',
    summary='Update specific setting (legacy)',
    description='Create or update setting (legacy endpoint)',
    status_code=status.HTTP_200_OK,
)
async def update_settings_legacy(
    *,
    locale: str,
    setting: MainSettings,
    token: Annotated[str, Depends(oauth2_scheme)],
    db=Depends(get_async_session),
):
    """Update Settings (legacy)."""
    _ = token
    async with db.begin() as transaction:
        setting = await repository.update_or_create_setting(
            locale=locale,
            setting=setting,
            transaction=transaction,
        )
        await transaction.commit()
        return setting


@verify_admin_async()
@settings.get(
    '/{settings_id}',
    summary='Get setting by ID',
    description='Get a specific setting by ID',
    status_code=status.HTTP_200_OK,
)
async def get_setting(
    *,
    settings_id: int,
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_async_session)],
) -> SettingsResponse:
    """Get setting by ID."""
    _ = token
    async with db.begin() as transaction:
        setting = await repository.get_setting_by_id(
            settings_id=settings_id,
            transaction=transaction,
        )

        if not setting:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Setting {settings_id} not found",
            )

        return _to_settings_response(setting)


@verify_admin_async()
@settings.post(
    '/',
    summary='Create setting',
    description='Create a new setting',
    status_code=status.HTTP_201_CREATED,
)
async def create_setting(
    *,
    setting_data: SettingsCreate,
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_async_session)],
) -> SettingsResponse:
    """Create a new setting."""
    _ = token
    async with db.begin() as transaction:
        setting = await repository.create_setting(
            setting_data=setting_data,
            transaction=transaction,
        )
        await transaction.commit()
        return _to_settings_response(setting)


@verify_admin_async()
@settings.patch(
    '/{settings_id}',
    summary='Update setting',
    description='Update an existing setting',
    status_code=status.HTTP_200_OK,
)
async def update_setting(
    *,
    settings_id: int,
    setting_data: SettingsUpdate,
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_async_session)],
) -> SettingsResponse:
    """Update setting."""
    _ = token
    async with db.begin() as transaction:
        try:
            setting = await repository.update_setting(
                settings_id=settings_id,
                setting_data=setting_data,
                transaction=transaction,
            )
            await transaction.commit()
            return _to_settings_response(setting)
        except repository.SettingsInputError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            ) from e


@verify_admin_async()
@settings.delete(
    '/{settings_id}',
    summary='Delete setting',
    description='Delete a setting',
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_setting(
    *,
    settings_id: int,
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_async_session)],
) -> None:
    """Delete setting."""
    _ = token
    async with db.begin() as transaction:
        deleted = await repository.delete_setting(
            settings_id=settings_id,
            transaction=transaction,
        )
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Setting {settings_id} not found",
            )
        await transaction.commit()
