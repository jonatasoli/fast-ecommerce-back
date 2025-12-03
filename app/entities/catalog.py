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


class CategoryCreate(BaseModel):
    """Category create schema."""

    name: str
    path: str
    menu: bool = False
    showcase: bool = False
    image_path: str | None = None


class CategoryUpdate(BaseModel):
    """Category update schema."""

    name: str | None = None
    path: str | None = None
    menu: bool | None = None
    showcase: bool | None = None
    image_path: str | None = None


class CategoryResponse(BaseModel):
    """Category response schema."""

    category_id: int
    name: str
    path: str
    menu: bool
    showcase: bool
    image_path: str | None
    model_config = ConfigDict(from_attributes=True)
