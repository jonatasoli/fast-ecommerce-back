from sqlalchemy.orm import Session
from fastapi import Header, APIRouter, Depends, File, UploadFile
from domains import domain_order
from ext import optimize_image
from schemas.order_schema import (
    OrderSchema,
    OrderFullResponse,
    ProductSchema,
    InstallmentSchema,
    CategorySchema,
    ProductFullResponse,
)
from endpoints.deps import get_db
from loguru import logger

product = APIRouter()

@product.post('/upload-image', status_code=200)
async def upload_image(image: UploadFile = File(...)):
    try:
        return  optimize_image.optimize_image(image)
    except Exception as e:
        raise e

@product.get("/showcase/all", status_code=200)
async def get_showcase(*, db: Session = Depends(get_db)):
    try:
        return domain_order.get_showcase(db)
    except Exception as e:
        logger.error(f"Erro em obter os produtos - { e }")
        raise e


@product.get("/{uri}", status_code=200)
async def get_product_uri(uri: str, db: Session = Depends(get_db)):
    try:
        return domain_order.get_product(db, uri)
    except Exception as e:
        logger.error(f"Erro em obter os produto - { e }")
        raise e

@product.get("/product/all", status_code=200)
async def get_products_all(db: Session = Depends(get_db)):
    try:
        return domain_order.get_product_all(db)
    except Exception as e:
        logger.error(f"Erro em obter os produtos - { e }")
        raise e


@product.post("/cart/installments", status_code=200)
async def get_installments(*, db: Session = Depends(get_db), cart: InstallmentSchema):
    try:
        return domain_order.get_installments(db, cart=cart)
    except Exception as e:
        logger.error(f"Erro ao coletar o parcelamento - {e}")
        raise e


@product.put("/update/{id}", status_code=200)
async def put_product(
    id: int, value: ProductFullResponse, db: Session = Depends(get_db)
):
    try:
        return domain_order.put_product(db, id, value)
    except Exception as e:
        raise e


@product.delete("/delete/{id}", status_code=200)
async def delete_product(id: int, db: Session = Depends(get_db)):
    try:
        return domain_order.delete_product(db, id)
    except Exception as e:
        raise e


@product.get("/category/all", status_code=200)
async def get_categorys(db: Session = Depends(get_db)):
    try:
        return domain_order.get_category()
    except Exception as e:
        logger.error(f"Erro em obter categoria - { e }")
        raise e


@product.get("/category/{id}", status_code=200)
async def get_product_category(*, db: Session = Depends(get_db), id):
    try:
        return domain_order.get_products_category(db, id)
    except Exception as e:
        raise e
