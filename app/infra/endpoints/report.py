from fastapi import APIRouter, Depends, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.report.entities import UserSalesComissions
from app.infra.deps import get_db
from domains import domain_user
from app.report import services


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
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> UserSalesComissions:
    """Get report sales comissions."""
    user = domain_user.get_affiliate(token)
    return await services.get_user_sales_comissions(
        user=user, paid=paid, db=db
    )
