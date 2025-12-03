import pytest
from pydantic import ValidationError

from app.entities.catalog import (
    Category,
    Categories,
    CategoryCreate,
    CategoryUpdate,
    CategoryResponse,
)


def test_category_create_valid():
    """Must create valid CategoryCreate schema."""
    # Arrange & Act
    category = CategoryCreate(
        name='Test Category',
        path='test-category',
        menu=True,
        showcase=False,
    )

    # Assert
    assert category.name == 'Test Category'
    assert category.path == 'test-category'
    assert category.menu is True
    assert category.showcase is False
    assert category.image_path is None


def test_category_create_with_defaults():
    """Must create CategoryCreate with default values."""
    # Arrange & Act
    category = CategoryCreate(
        name='Test Category',
        path='test-category',
    )

    # Assert
    assert category.menu is False
    assert category.showcase is False
    assert category.image_path is None


def test_category_create_missing_required_field():
    """Must raise ValidationError when missing required fields."""
    # Act & Assert
    with pytest.raises(ValidationError) as exc_info:
        CategoryCreate(name='Test Category')

    assert 'path' in str(exc_info.value)


def test_category_update_partial():
    """Must allow partial updates in CategoryUpdate."""
    # Arrange & Act
    update = CategoryUpdate(name='Updated Name')

    # Assert
    assert update.name == 'Updated Name'
    assert update.path is None
    assert update.menu is None
    assert update.showcase is None


def test_category_update_all_fields():
    """Must update all fields in CategoryUpdate."""
    # Arrange & Act
    update = CategoryUpdate(
        name='Updated Category',
        path='updated-path',
        menu=True,
        showcase=True,
        image_path='https://cdn.test.com/image.png',
    )

    # Assert
    assert update.name == 'Updated Category'
    assert update.path == 'updated-path'
    assert update.menu is True
    assert update.showcase is True
    assert update.image_path == 'https://cdn.test.com/image.png'


def test_category_response_valid():
    """Must create valid CategoryResponse schema."""
    # Arrange & Act
    response = CategoryResponse(
        category_id=1,
        name='Test Category',
        path='test-category',
        menu=True,
        showcase=False,
        image_path=None,
    )

    # Assert
    assert response.category_id == 1
    assert response.name == 'Test Category'
    assert response.path == 'test-category'


def test_category_model_validate():
    """Must validate category from attributes."""
    # Arrange
    from app.infra.models import CategoryDB

    db_category = CategoryDB(
        category_id=1,
        name='Test Category',
        path='test-category',
        menu=True,
        showcase=False,
        image_path=None,
    )

    # Act
    category = Category.model_validate(db_category)

    # Assert
    assert category.category_id == 1
    assert category.name == 'Test Category'


def test_categories_list():
    """Must create Categories with list of Category."""
    # Arrange
    category_list = [
        Category(
            category_id=1,
            name='Category 1',
            path='category-1',
            menu=True,
            showcase=False,
            image_path=None,
        ),
        Category(
            category_id=2,
            name='Category 2',
            path='category-2',
            menu=False,
            showcase=True,
            image_path=None,
        ),
    ]

    # Act
    categories = Categories(categories=category_list)

    # Assert
    assert len(categories.categories) == 2
    assert categories.categories[0].name == 'Category 1'
    assert categories.categories[1].name == 'Category 2'
