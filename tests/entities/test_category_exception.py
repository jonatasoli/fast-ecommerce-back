import pytest

from app.entities.category import CategoryNotFoundError, CategoryMediaNotFoundError


def test_category_not_found_error_default_message():
    # Act
    error = CategoryNotFoundError()

    # Assert
    assert str(error) == 'Category not found'
    assert error.message == 'Category not found'


def test_category_not_found_error_custom_message():
    # Setup
    custom_message = 'Custom category not found message'

    # Act
    error = CategoryNotFoundError(custom_message)

    # Assert
    assert str(error) == custom_message
    assert error.message == custom_message


def test_category_not_found_error_is_exception():
    # Act
    error = CategoryNotFoundError()

    # Assert
    assert isinstance(error, Exception)


def test_category_not_found_error_can_be_raised():
    with pytest.raises(CategoryNotFoundError) as exc_info:
        raise CategoryNotFoundError('Test error')

    assert str(exc_info.value) == 'Test error'


def test_category_media_not_found_error_default_message():
    # Act
    error = CategoryMediaNotFoundError()

    # Assert
    assert str(error) == 'Media not found in category gallery'
    assert error.message == 'Media not found in category gallery'


def test_category_media_not_found_error_custom_message():
    # Setup
    custom_message = 'Custom media not found message'

    # Act
    error = CategoryMediaNotFoundError(custom_message)

    # Assert
    assert str(error) == custom_message
    assert error.message == custom_message


def test_category_media_not_found_error_is_exception():
    # Act
    error = CategoryMediaNotFoundError()

    # Assert
    assert isinstance(error, Exception)


def test_category_media_not_found_error_can_be_raised():
    with pytest.raises(CategoryMediaNotFoundError) as exc_info:
        raise CategoryMediaNotFoundError('Test media error')

    assert str(exc_info.value) == 'Test media error'
