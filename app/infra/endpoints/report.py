from requests.models import HTTPError
from app.entities.user import UserNotAdminError
from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.infra.database import get_async_session
from app.report import services
from app.entities.report import (
    CommissionInDB,
    CommissionInDB,
    InformUserProduct,
    UserSalesCommissions,
)
from app.user import services as domain_user

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='access_token')

report = APIRouter(
    prefix='/report',
    tags=['report'],
)


@report.get(
    '/user/comissions',
    summary='Get user sales commissions',
    description='Return sales commissions to user is filter sales or not paid sales',
    status_code=status.HTTP_200_OK,
    response_model=UserSalesCommissions,
)
async def get_user_sales_comissions(
    *,
    paid: bool = False,
    released: bool = False,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_async_session),
) -> list[CommissionInDB | None]:
    """Get report sales comissions."""
    async with db() as session:
        user = await domain_user.get_affiliate_by_token(token, db=session)
        return await services.get_user_sales_comissions(
            user=user,
            paid=paid,
            released=released, db=session,
        )


@report.post(
    '/inform',
    summary='receive the user phone and e-mail and send to administrators',
    description='Sent e-mail to admins to inform the user would like know\
        when product is back',
    status_code=status.HTTP_204_NO_CONTENT,
)
async def inform_product_user(
        *,
        inform: InformUserProduct,
        token: str = Depends(oauth2_scheme),
        db = Depends(get_async_session),
):
    """Get user and product and inform admins."""
    async with db() as session:
        if not (_ := domain_user.get_admin(token, db=session)):
            raise UserNotAdminError
        return await services.notify_product_to_admin(
            inform=inform,
            db=session,
        )
