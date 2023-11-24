from app.infra.models import CategoryDB
from sqlalchemy.orm import SessionTransaction
from sqlalchemy import select


async def get_categories(
    menu: bool,
    showcase: bool,
    transaction: SessionTransaction,
) -> list[CategoryDB]:
    """Get categories by filters."""
    categorys_query = select(CategoryDB)
    if menu:
        categorys_query = categorys_query.where(CategoryDB.menu is True)
    if showcase:
        categorys_query = categorys_query.where(CategoryDB.showcase is True)
    return await transaction.session.scalars(categorys_query)
