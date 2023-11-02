from typing import Any
from app.entities.user import UserCouponResponse, CredentialError
from app.infra.models.users import User
from jose import JWTError, jwt
from config import settings


def get_affiliate_urls(user: User, base_url: str) -> UserCouponResponse:
    """Get affiliate user and return code urls."""
    _ = user
    _urls = []
    for _id in range(10):
        _urls.append(f'{base_url}/?affiliate={_id}')
    return UserCouponResponse(urls=_urls)


def verify_token_user_is_valid(token: str, bootstrap: Any) -> None:
    """Verify if token user is valid."""
    user = bootstrap.user.get_current_user(token)
    if not user:
        raise CredentialError


def get_current_user(
    token: str,
    bootstrap: Any,
) -> User:
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
