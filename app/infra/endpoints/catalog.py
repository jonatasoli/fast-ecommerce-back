from typing import Any
from fastapi import APIRouter, Depends, status
from app.catalog.entities import Categories
from app.catalog.services import get_categories_by_filter
from app.entities.product import ProductsResponse
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


@catalog.get(
    '/showcase/all',
    summary='Get products in showcase',
    description='Return all products in flag with shoucase in ProductDB',
    status_code=status.HTTP_200_OK,
)
def get_showcase(*, db: Session = Depends(get_db)) -> Any:
    """Get showcase."""
    try:
        return domain_order.get_showcase(db)
    except Exception as e:
        logger.error(f'Erro em obter os produtos - { e }')
        raise


@catalog.get(
    '/all',
    summary='Get all products',
    description='Return all products in ProductDB',
    status_code=status.HTTP_200_OK,
    response_model=ProductsResponse,
)
def get_products_all(
    offset: int = 10, page: int = 1, db: Session = Depends(get_db)
) -> ProductsResponse:
    """Get products all."""

    return domain_order.get_product_all(page=page, offset=offset, db=db)


@catalog.get(
    '/latest',
    summary='Get latest products',
    description='Return latest add products in ProductDB',
    status_code=status.HTTP_200_OK,
    response_model=ProductsResponse,
)
def get_latest_products(
    offset: int = 10, page: int = 1, db: Session = Depends(get_db)
) -> ProductsResponse:
    """Get latest products."""

    return domain_order.get_latest_products(page=page, offset=offset, db=db)


@catalog.get(
    '/featured',
    summary='Get featured products',
    description='Return products is flagged with feature in ProductDB limited for offset',
    status_code=status.HTTP_200_OK,
    response_model=ProductsResponse,
)
def get_products_all(
    offset: int = 2, page: int = 1, db: Session = Depends(get_db)
) -> ProductsResponse:
    """Get products all."""

    return domain_order.get_featured_products(page=page, offset=offset, db=db)


@catalog.get(
    '/',
    summary='Get searched term products',
    description='Return products with machted term in ProductDB',
    status_code=status.HTTP_200_OK,
    response_model=ProductsResponse,
)
def search_products(
    search: str, offset: int = 2, page: int = 1, db: Session = Depends(get_db)
) -> ProductsResponse:
    """Get search term products."""

    return domain_order.search_products(
        search=search, offset=offset, page=page, db=db
    )


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
    offset: int = 2,
    page: int = 1,
    db: Session = Depends(get_db),
) -> None:
    """Get product category."""
    try:
        return domain_order.get_products_category(
            offset=offset, page=page, path=path, db=db
        )
    except Exception:
        raise
