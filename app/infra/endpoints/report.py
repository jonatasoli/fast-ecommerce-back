from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.infra.database import get_async_session
from app.report import services
from app.report.entities import UserSalesComissions
from domains import domain_user

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='access_token')

report = APIRouter(
    prefix='/report',
    tags=['report'],
)


@report.get(
    '/user/comissions',
    summary='Get user sales commissions',
    description='Return sales commissions to user is possible filter all sales or not paid sales',
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
    user = domain_user.get_affiliate(token)
    return await services.get_user_sales_comissions(
        user=user, paid=paid, released=released, db=db
    )
