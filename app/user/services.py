# ruff: noqa: ANN401
from datetime import datetime, timedelta
from typing import Any
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from propan.brokers.rabbit import RabbitQueue

from sqlalchemy import select
from app.entities.user import UserCouponResponse, CredentialError
from app.infra.models import UserDB, CouponsDB, UserResetPasswordDB
from jose import JWTError, jwt
from config import settings
from sqlalchemy.orm import Session, sessionmaker

from schemas.user_schema import UserResponseResetPassword

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='access_token')


def get_affiliate_urls(
    user: UserDB,
    db: Session,
    base_url: str,
) -> UserCouponResponse:
    """Get affiliate user and return code urls."""
    _urls = []
    with db:
        coupons = db.query(CouponsDB).filter(
            CouponsDB.affiliate_id == user.user_id,
        )
        for coupon in coupons:
            _urls.append(f'{base_url}?coupon={coupon.code}')
    return UserCouponResponse(urls=_urls)


def verify_token_user_is_valid(token: str, bootstrap: Any) -> None:
    """Verify if token user is valid."""
    user = bootstrap.user.get_current_user(token)
    if not user:
        raise CredentialError


def get_current_user(
    token: str,
    bootstrap: Any,
) -> UserDB:
    """Must return user db."""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        document = payload.get('sub')
        if document is None:
            raise CredentialError
    except JWTError:
        raise CredentialError from JWTError

    user = bootstrap.user_uow.get_user_by_document(document=document)
    if user is None:
        raise CredentialError
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    """Create temporary access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({'exp': expire})
    return jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


async def save_token_reset_password(document: str, *, message, db) -> None:
    """Create request to reset password."""
    access_token_expires = timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    )
    _token = create_access_token(
        data={'sub': document},
        expires_delta=access_token_expires,
    )
    with db() as session:
        user_query = select(UserDB).where(UserDB.document == document)
        _user = session.scalar(user_query)
        db_reset = UserResetPasswordDB(user_id=_user.user_id, token=_token)
        session.add(db_reset)
        session.commit()
        await message.broker.publish(
            {
                'mail_to': _user.email,
                'token': _token,
            },
            queue=RabbitQueue('reset_password_request'),
        )


def reset_password(
    token: str,
    *,
    db: sessionmaker,
    data: UserResponseResetPassword,
) -> None:
    """Reset password with token created."""
    pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
    with db() as session:
        user_query = select(UserDB).where(UserDB.document == data.document)
        _user = session.scalar(user_query)

        used_token_query = select(UserResetPasswordDB).where(
            UserResetPasswordDB.user_id == _user.user_id,
            UserResetPasswordDB.token == token,
        )
        _used_token = session.scalar(used_token_query)

        _used_token.used_token = True
        _user.password = pwd_context.hash(data.password)
        session.commit()
