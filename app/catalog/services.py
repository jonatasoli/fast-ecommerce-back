from typing import Any

from app.catalog.entities import Categories


async def get_categories_by_filter(
    menu: bool,
    showcase: bool,
    bootstrap: Any,
) -> Categories:
    return await bootstrap.catalog_uow.get_categories(
        menu=menu,
        showcase=showcase,
        bootstrap=bootstrap,
    )
