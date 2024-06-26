from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.infra.database import get_async_session
from app.report import services
from app.entities.report import UserSalesComissions
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
    response_model=UserSalesComissions,
)
async def get_user_sales_comissions(
    *,
    paid: bool = False,
    released: bool = False,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_async_session),
) -> UserSalesComissions:
    """Get report sales comissions."""
    async with db() as session:
        user = await domain_user.get_affiliate_by_token(token, db=session)
        return await services.get_user_sales_comissions(
            user=user,
            paid=paid,
            released=released,
            db=session,
        )
