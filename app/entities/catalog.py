from pydantic import BaseModel, ConfigDict


class Category(BaseModel):
    """Category entity."""

    category_id: int
    name: str
    path: str
    menu: bool
    showcase: bool
    image_path: str | None
    model_config = ConfigDict(from_attributes=True)


class Categories(BaseModel):
    """Categories entity."""

    categories: list[Category]
    model_config = ConfigDict(from_attributes=True)
