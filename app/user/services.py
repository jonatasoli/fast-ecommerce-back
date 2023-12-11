from typing import Any
from app.entities.user import UserCouponResponse, CredentialError
from app.infra.models import UserDB, CouponsDB
from jose import JWTError, jwt
from config import settings
from sqlalchemy.orm import Session


def get_affiliate_urls(user: UserDB, db: Session, base_url: str) -> UserCouponResponse:
    """Get affiliate user and return code urls."""
    _urls = []
    with db:
        coupons = db.query(CouponsDB).filter(CouponsDB.affiliate_id == user.user_id)
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
