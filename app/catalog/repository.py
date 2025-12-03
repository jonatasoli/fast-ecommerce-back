from app.infra.models import CategoryDB, CategoryMediaGalleryDB
from app.entities.category import CategoryNotFoundError
from sqlalchemy.orm import SessionTransaction
from sqlalchemy import select, delete


async def get_categories(
    *,
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

async def get_category_by_id(
    category_id: int,
    transaction: SessionTransaction,
) -> CategoryDB | None:
    """Get category by ID."""
    query = select(CategoryDB).where(CategoryDB.category_id == category_id)
    result = await transaction.session.execute(query)
    return result.scalar_one_or_none()


async def create_category(
    category_data: dict,
    transaction: SessionTransaction,
) -> CategoryDB:
    """Create new category."""
    db_category = CategoryDB(**category_data)
    transaction.session.add(db_category)
    await transaction.session.flush()
    return db_category


async def update_category(
    category_id: int,
    category_data: dict,
    transaction: SessionTransaction,
) -> CategoryDB:
    """Update category."""
    db_category = await get_category_by_id(category_id, transaction)
    if not db_category:
        raise CategoryNotFoundError

    for field, value in category_data.items():
        setattr(db_category, field, value)

    await transaction.session.flush()
    return db_category


async def delete_category(
    category_id: int,
    transaction: SessionTransaction,
) -> None:
    """Delete category."""
    db_category = await get_category_by_id(category_id, transaction)
    if not db_category:
        raise CategoryNotFoundError

    # Delete associated media gallery entries
    delete_stmt = delete(CategoryMediaGalleryDB).where(
        CategoryMediaGalleryDB.category_id == category_id,
    )
    await transaction.session.execute(delete_stmt)

    await transaction.session.delete(db_category)
    await transaction.session.flush()
