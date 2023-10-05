

from app.entities.user import UserCouponResponse
from app.infra.models.users import User


def get_affiliate_urls(user: User, base_url: str):
    _urls = []
    for id in range(10):
        _urls.append(f"{base_url}/?affiliate={id}")
    return UserCouponResponse(urls=_urls)
