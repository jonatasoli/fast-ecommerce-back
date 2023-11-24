from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.infra import deps
from schemas.order_schema import CheckoutReceive, ProductSchema

direct_sales = APIRouter()


@direct_sales.get('/product/{uri}', status_code=200)
async def get_product(
    *,
    db: Session = Depends(deps.get_db),
    uri: None,
) -> None:
    """Get product."""
    ...


@direct_sales.get('/upsell/{id}', status_code=200)
async def get_upsell_products() -> None:
    """Get upsell products."""
    ...


@direct_sales.post('/checkout', status_code=201)
def checkout(
    *,
    db: Session = Depends(deps.get_db),
    data: CheckoutReceive,
) -> None:
    """Checkout."""
    ...


@direct_sales.post('/create-product', status_code=201)
async def create_product(
    *,
    db: Session = Depends(deps.get_db),
    product_data: ProductSchema,
) -> None:
    """Create product."""
    ...
