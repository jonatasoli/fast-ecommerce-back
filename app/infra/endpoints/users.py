from datetime import timedelta
from typing import Any, Annotated

from app.infra.worker import task_message_bus

from config import settings
from fastapi import APIRouter, Depends, Request, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session, sessionmaker

from app.entities.user import (
    UserCouponResponse,
    UserFilters,
    UserInDB,
    UserSchema,
    UserUpdate,
    UsersDBResponse,
)
from app.infra.bootstrap.user_bootstrap import Command, bootstrap
from loguru import logger
from app.infra.database import get_async_session, get_session

from app.infra.deps import get_db
from app.entities.user import (
    SignUp,
    SignUpResponse,
    Token,
    UserResponseResetPassword,
)
from app.user import repository, services
from app.entities.user import CredentialError


async def get_bootstrap() -> Command:
    """Get bootstrap."""
    return await bootstrap()


user = APIRouter(
    prefix='/user',
    tags=['user'],
)
users = APIRouter(
    prefix='/users',
    tags=['users'],
)


oauth2_scheme = OAuth2PasswordBearer(tokenUrl='access_token')


@user.get(
    '/affiliate',
    summary='Get user affiliate coupons',
    description='Return coupons to affiliated user',
    status_code=status.HTTP_200_OK,
)
async def get_affiliate_user(
    *,
    request: Request,
    token: Annotated[str, Depends(oauth2_scheme)],  # noqa: ERA001
    db: Annotated[Session, Depends(get_session)],
) -> UserCouponResponse:
    """Get user."""
    user = services.get_affiliate(token, db=db)
    logger.info(user.user_id)
    base_url = settings.FRONTEND_URLS or str(request.base_url)
    return services.get_affiliate_urls(
        user=user,
        db=db,
        base_url=base_url,
    )


@user.post(
    '/signup',
    status_code=status.HTTP_201_CREATED,
)
def signup(
    *,
    db=Depends(get_session),
    user_in: SignUp,
) -> SignUpResponse:
    """Signup."""
    return services.create_user(db, obj_in=user_in)


@user.post('/token')
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[Session, Depends(get_session)],
) -> dict[str, str | Any]:
    """Login for access token."""
    user = services.authenticate_user(
        db,
        form_data.username,
        form_data.password,
    )
    access_token_expires = timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    )
    access_token = services.create_access_token(
        data={'sub': user.document},
        expires_delta=access_token_expires,
    )
    role = services.get_role_user(db, user.role_id)

    return {
        'access_token': access_token,
        'token_type': 'bearer',
        'role': role,
    }


@user.get(
    '/token',
    summary='Verify token',
    description='Send token to verify if is valid yet.',
    status_code=status.HTTP_204_NO_CONTENT,
)
async def verify_token_is_valid(
    *,
    req: Request,
    db: Annotated[Session, Depends(get_db)],
) -> None:
    """Check for access token is valid."""
    _ = db
    if token := req.headers.get('authorization'):  # noqa: SIM102
        if token.split()[1] != 'undefined':
            logger.info(token)
            return
    raise CredentialError


@user.get(
    '/{document}',
    status_code=status.HTTP_200_OK,
)
async def get_user(
    document: str,
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[sessionmaker, Depends(get_session)],
) -> UserSchema:
    """Get user."""
    _document = document
    return services.get_current_user(token, db=db)


@user.post('/request-reset-password', status_code=status.HTTP_204_NO_CONTENT)
async def request_reset_password(
    document: str,
    db: Annotated[sessionmaker, Depends(get_session)],
) -> None:
    """Request reset password."""
    message = task_message_bus
    await services.save_token_reset_password(document, message=message, db=db)


@user.patch('/reset-password', status_code=status.HTTP_204_NO_CONTENT)
async def reset_password(
    response_model: UserResponseResetPassword,
    token: str,
    db: Annotated[sessionmaker, Depends(get_session)],
) -> None:
    """Reset password."""
    services.reset_password(token, db=db, data=response_model)


@user.patch(
    '/{user_id}',
    status_code=status.HTTP_200_OK,
)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[sessionmaker, Depends(get_async_session)],
) -> UserInDB:
    """Update user."""
    await services.verify_admin(
        token=token,
        db=db,
    )
    return await services.update_user(
        user_id,
        update_user=user_update,
        db=db,
    )


@user.get(
    '/{user_id}',
    status_code=status.HTTP_200_OK,
)
async def get_user_by_id(
    user_id: int,
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[sessionmaker, Depends(get_async_session)],
) -> UserInDB:
    """Get user."""
    await services.verify_admin(
        token=token,
        db=db,
    )
    return await services.get_user_by_id(user_id, db=db)


@users.get(
    '/',
    status_code=status.HTTP_200_OK,
)
async def get_users(
    token: Annotated[str, Depends(oauth2_scheme)],
    filters: Annotated[UserFilters, Depends(UserFilters)],
    db: Annotated[sessionmaker, Depends(get_async_session)],
) -> UsersDBResponse:
    """Get user."""
    await services.verify_admin(
        token=token,
        db=db,
    )
    async with db().begin() as transaction:
        return await repository.get_users(
            filters=filters,
            transaction=transaction,
        )


@users.get(
    '/affiliate',
    status_code=status.HTTP_200_OK,
)
async def get_affiliate_users(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[sessionmaker, Depends(get_async_session)],
) -> UsersDBResponse:
    """Get user."""
    await services.verify_admin(
        token=token,
        db=db,
    )
    async with db().begin() as transaction:
        return await repository.get_affiliate_users(
            transaction=transaction,
        )
