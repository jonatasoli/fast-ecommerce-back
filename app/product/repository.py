from sqlalchemy import select
from sqlalchemy.orm import Session

from app.infra.models import ProductDB


def get_product_by_id(product_id: int, *, db: Session):
    return db.scalar(
        select(ProductDB).where(ProductDB.product_id == product_id),
    )
