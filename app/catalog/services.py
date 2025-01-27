# ruff: noqa: ANN401 FBT001
from typing import Any

from app.entities.catalog import Categories, Category
from app.catalog import repository as catalog_repository


async def get_categories_by_filter(
    menu: bool,
    showcase: bool,
    db: Any,
) -> Categories:
    """Must return all categories in catalog."""
    categories = []
    async with db().begin() as transaction:
        categories_db = await catalog_repository.get_categories(
            menu=menu,
            showcase=showcase,
            transaction=transaction,
        )
    for category in categories_db:
        categories.append(Category.model_validate(category))
    return Categories(categories=categories)
