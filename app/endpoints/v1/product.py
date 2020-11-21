from sqlalchemy.orm import Session
from fastapi import Header, APIRouter, Depends
from domains import domain_order
from schemas.order_schema import OrderSchema, OrderFullResponse, ProductSchema
from endpoints.deps import get_db
from loguru import logger

product = APIRouter()


@product.get('/product/showcase/all', status_code=200)
async def get_showcase(
        *,
        db: Session = Depends(get_db)
        ):
    try:
        return domain_order.get_showcase(db)
    except Exception as e:
        logger.error(f"Erro em obter os produtos - { e }")
        raise e
