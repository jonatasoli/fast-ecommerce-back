from datetime import timedelta
from typing import Dict, Any

from dynaconf import settings
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session, InstrumentedAttribute
from sqlalchemy.orm.base import _T_co

from app.entities.user import UserCouponResponse
from app.infra.bootstrap.user_bootstrap import Command, bootstrap
from loguru import logger

from domains import domain_user
from domains.domain_user import check_token
from app.infra.deps import get_db
from schemas.user_schema import (
    SignUp,
    SignUpResponse,
    Token,
    UserResponseResetPassword,
)
from app.user import services
from app.entities.user import CredentialError


async def get_bootstrap() -> Command:
    """Get bootstrap."""
    return await bootstrap()


user = APIRouter(
    prefix='/user',
    tags=['user'],
)


oauth2_scheme = OAuth2PasswordBearer(tokenUrl='access_token')


@user.get(
    '/affiliate',
    summary='Get user affiliate coupons',
    description='Return coupons to affiliated user',
    status_code=status.HTTP_200_OK,
    response_model=UserCouponResponse,
)
async def get_affiliate_user(
    *,
    request: Request,
    # token: str = Depends(oauth2_scheme), # TODO : uncomment when remove the mock
    db: Session = Depends(get_db),
) -> UserCouponResponse:
    """Get user."""
    token = await login_for_access_token(
        form_data=OAuth2PasswordRequestForm(
            username=settings.USERNAME, password=settings.PASSWORD
        ),
        db=db,
    )   # TODO : mock to be removed
    token = token.get('access_token')
    user = domain_user.get_affiliate(token)
    return services.get_affiliate_urls(
        user=user, db=db, base_url=str(request.base_url)
    )


@user.post('/signup', status_code=201, response_model=SignUpResponse)
def signup(
    *,
    db: Session = Depends(get_db),
    user_in: SignUp,
) -> dict[str, str]:
    """Signup."""
    user = domain_user.create_user(db, obj_in=user_in)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Não foi possível criar o usuário',
        )
    return {'name': 'usuario', 'message': 'adicionado com sucesso'}


@user.get('/dashboard', status_code=200)
@check_token
def dashboard(
    *,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
) -> dict[str, Any]:
    """Dashboard."""
    user = domain_user.get_current_user(token)
    role = domain_user.get_role_user(db, user.role_id)
    return {'role': role}


@user.post('/token', response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> dict[str, str | Any]:
    """Login for access token."""
    user = domain_user.authenticate_user(
        db,
        form_data.username,
        form_data.password,
    )
    access_token_expires = timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    )
    access_token = domain_user.create_access_token(
        data={'sub': user.document},
        expires_delta=access_token_expires,
    )
    role = domain_user.get_role_user(db, user.role_id)

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
    db: Session = Depends(get_db),
) -> None:
    """Check for access token is valid."""
    _ = db
    if token := req.headers.get('authorization'):
        if token.split()[1] != 'undefined':
            logger.info(token)
            return
    raise CredentialError


@user.get('/{document}', status_code=200)
async def get_user(
    document: str,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> None:
    """Get user."""
    domain_user.get_current_user(token)
    return domain_user.get_user_login(db, document)


@user.post('/request-reset-password', status_code=200)
async def request_reset_password(
    document: str,
    db: Session = Depends(get_db),
) -> None:
    """Request reset password."""
    return domain_user.save_token_reset_password(db, document)


@user.put('/reset-password', status_code=200)
async def reset_password(
    response_model: UserResponseResetPassword,
    db: Session = Depends(get_db),
) -> None:
    """Reset password."""
    return domain_user.reset_password(db, data=response_model)
