from pydantic import BaseModel, ConfigDict


class Category(BaseModel):
    """Category entity."""

    name: str
    path: str
    menu: bool
    showcase: bool
    model_config = ConfigDict(from_attributes=True)


class Categories(BaseModel):
    """Categories entity."""

    categories: list[Category]
    model_config = ConfigDict(from_attributes=True)
