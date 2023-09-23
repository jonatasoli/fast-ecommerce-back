from typing import Any
from fastapi import APIRouter, Depends, status
from app.catalog.entities import Categories
from app.catalog.services import get_categories_by_filter
from app.infra.bootstrap.catalog_bootstrap import Command, bootstrap
from domains import domain_order
from sqlalchemy.orm import Session

from loguru import logger

from app.infra import deps
from app.infra.deps import get_db

catalog = APIRouter(
    prefix='/catalog',
    tags=['catalog'],
)


async def get_bootstrap() -> Command:
    """Get bootstrap."""
    return await bootstrap()


@catalog.get('/showcase/all', status_code=200)
def get_showcase(*, db: Session = Depends(get_db)) -> Any:
    """Get showcase."""
    try:
        return domain_order.get_showcase(db)
    except Exception as e:
        logger.error(f'Erro em obter os produtos - { e }')
        raise


@catalog.get('/all', status_code=200)
def get_products_all(db: Session = Depends(get_db)) -> Any:
    """Get products all."""
    try:
        return domain_order.get_product_all(db)
    except Exception as e:
        logger.error(f'Erro em obter os produtos - { e }')
        raise


@catalog.get('/', status_code=200)
def get_products_all(search: str, db: Session = Depends(get_db)) -> Any:
    """Get products all."""
    try:
        return domain_order.search_products(search, db)
    except Exception as e:
        logger.error(f'Erro em obter os produtos - { e }')
        raise


@catalog.get(
    '/categories',
    status_code=status.HTTP_200_OK,
    response_model=Categories,
)
async def get_categories(
    menu: bool = False,
    showcase: bool = False,
    bootstrap: Command = Depends(get_bootstrap),
) -> Categories:
    """GET categories."""
    try:
        return await get_categories_by_filter(
            menu=menu,
            showcase=showcase,
            bootstrap=bootstrap,
        )
    except Exception as e:
        logger.error(f'Erro em obter as categorias - { e }')
        raise


@catalog.get('/category/products/{path}', status_code=200)
def get_product_category(
    path: str,
    db: Session = Depends(get_db),
) -> None:
    """Get product category."""
    try:
        return domain_order.get_products_category(db, path)
    except Exception:
        raise
