
from fastapi.exceptions import HTTPException
from app.entities.settings import MainSettings
from app.entities.user import UserNotAdminError, UserNotFoundError
from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordBearer

from app.infra.database import get_async_session
from app.settings import repository
from app.user import services as domain_user
from app.user.services import verify_admin_async

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='access_token')

settings = APIRouter(
    prefix='/settings',
    tags=['settings'],
)


@verify_admin_async()
@settings.get(
    '/',
    summary='Get settings',
    description='get a settings for field and locale',
    status_code=status.HTTP_200_OK,
)
async def get_settings(
    *,
    field: str,
    locale: str,
    token: str = Depends(oauth2_scheme),
    db = Depends(get_async_session),
):
    """Get Setting."""
    _ = token
    async with db.begin() as transaction:
        return await repository.get_settings(
            locale=locale,
            field=field,
            transaction=transaction,
        )


@verify_admin_async()
@settings.patch(
    '/',
    summary='Update specific setting',
    description='Create or update setting',
    status_code=status.HTTP_200_OK,
)
@verify_admin_async()
async def inform_product_user(
    *,
    locale: str,
    setting: MainSettings,
    token: str = Depends(oauth2_scheme),
    db = Depends(get_async_session),
):
    """Update Settings."""
    _ = token
    async with db.begin() as transaction:
        setting = await repository.update_or_create_setting(
            locale=locale,
            setting=setting,
            transaction=transaction,
        )
        await transaction.commit()
        return setting
