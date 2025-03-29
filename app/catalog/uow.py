from typing import Any
from app.entities.catalog import Categories, Category
from app.catalog import repository as catalog_repository


async def get_categories(
    *,
    menu: bool,
    showcase: bool,
    db: Any,
) -> Categories:
    """Get categories by filters."""
    categories = []
    async with db().begin() as transaction:
        categories_db = await catalog_repository.get_categories(
            menu,
            showcase,
            transaction,
        )
    for category in categories_db:
        categories.append(Category.model_validate(category))
    return Categories(categories=categories)
