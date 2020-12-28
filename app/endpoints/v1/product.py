from sqlalchemy.orm import Session
from fastapi import Header, APIRouter, Depends
from domains import domain_order
from schemas.order_schema import OrderSchema, OrderFullResponse,\
        ProductSchema, InstallmentSchema, CategorySchema
from endpoints.deps import get_db
from loguru import logger

product = APIRouter()


@product.get('/showcase/all', status_code=200)
async def get_showcase(
        *,
        db: Session = Depends(get_db)
        ):
    try:
        return domain_order.get_showcase(db)
    except Exception as e:
        logger.error(f"Erro em obter os produtos - { e }")
        raise e


@product.get('/{id}', status_code=200)
async def get_product_id(
        *,
        db: Session = Depends(get_db),
        id
        ):
    try:
        return domain_order.get_product_by_id(db, id)
    except Exception as e:
        logger.error(f"Erro em obter os produto - { e }")
        raise e

@product.post('/cart/installments', status_code=200)
async def get_installments(
        *,
        db: Session = Depends(get_db),
        cart: InstallmentSchema
        ):
    try:
        return domain_order.get_installments(db, cart=cart)
    except Exception as e:
        logger.error(f"Erro ao coletar o parcelamento - {e}")
        raise e


@product.get('/category/all', status_code=200)
async def get_category(
        *,
        db: Session = Depends(get_db)
        ):
    try:
        return domain_order.get_category(db)
    except Exception as e:
        raise e


@product.get('/category/{id}', status_code=200)
async def get_product_category(
        *,
        db: Session = Depends(get_db),
        id
        ):
    try:
        return domain_order.get_products_category(db, id)
    except Exception as e:
        raise e