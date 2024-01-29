# ruff: noqa: ANN401 FBT001
from typing import Any

from app.catalog.entities import Categories


async def get_categories_by_filter(
    menu: bool,
    showcase: bool,
    bootstrap: Any,
) -> Categories:
    """Must return all categories in catalog."""
    return await bootstrap.catalog_uow.get_categories(
        menu=menu,
        showcase=showcase,
        bootstrap=bootstrap,
    )
