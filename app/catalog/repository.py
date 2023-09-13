from app.infra.models.order import Category
from sqlalchemy.orm import SessionTransaction
from sqlalchemy import select


async def get_categories(
    menu: bool,
    showcase: bool,
    transaction: SessionTransaction,
) -> list[Category]:
    """Get categories by filters."""
    categorys_query = select(Category)
    if menu:
        categorys_query = categorys_query.where(Category.menu is True)
    if showcase:
        categorys_query = categorys_query.where(Category.showcase is True)
    return await transaction.session.scalars(categorys_query)
