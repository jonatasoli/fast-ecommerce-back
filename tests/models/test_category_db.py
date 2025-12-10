from sqlalchemy import select
from app.infra.models import CategoryDB
from tests.factories_db import CategoryFactory


def test_create_category(session):
    # Setup
    new_category = CategoryFactory()
    session.add(new_category)
    session.commit()

    # Act
    category = session.scalar(
        select(CategoryDB).where(CategoryDB.category_id == new_category.category_id),
    )

    assert category.category_id is not None
    assert category.name == new_category.name
    assert category.path == new_category.path
    assert category == new_category


def test_category_default_values(session):
    # Setup
    new_category = CategoryFactory(menu=False, showcase=False)
    session.add(new_category)
    session.commit()

    # Act
    category = session.scalar(
        select(CategoryDB).where(CategoryDB.category_id == new_category.category_id),
    )

    assert category.menu is False
    assert category.showcase is False


def test_category_with_image_path(session):
    # Setup
    image_path = 'https://cdn.test.com/category.png'
    new_category = CategoryFactory(image_path=image_path)
    session.add(new_category)
    session.commit()

    # Act
    category = session.scalar(
        select(CategoryDB).where(CategoryDB.category_id == new_category.category_id),
    )

    assert category.image_path == image_path
