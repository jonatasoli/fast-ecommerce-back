import pytest
from app.entities.freight import (
    FreightPackage,
    MetricError,
    calculate_package,
    raise_metric_error,
    MAX_LENGTH,
    MAX_WIDTH,
    MAX_HEIGHT,
    MIN_LENGTH,
    MIN_WIDTH,
    MIN_HEIGHT,
)
from tests.factories import ProductInDBFactory


def test_raise_metric_error_should_raise():
    """Must raise MetricError."""
    # Act / Assert
    with pytest.raises(MetricError):
        raise_metric_error()


def test_calculate_package_with_valid_products():
    """Must calculate package dimensions correctly."""
    # Arrange
    product1 = ProductInDBFactory(weight=1000, length=20, width=15, height=10, diameter=0)
    product2 = ProductInDBFactory(weight=500, length=10, width=10, height=5, diameter=0)
    products = [product1, product2]

    # Act
    package = calculate_package(products)

    # Assert
    assert isinstance(package, FreightPackage)
    assert package.weight == "1500"
    assert float(package.length) >= MIN_LENGTH
    assert float(package.width) >= MIN_WIDTH
    assert float(package.height) >= MIN_HEIGHT


def test_calculate_package_with_minimum_dimensions():
    """Must enforce minimum package dimensions."""
    # Arrange
    product = ProductInDBFactory(weight=100, length=1, width=1, height=1, diameter=0)
    products = [product]

    # Act
    package = calculate_package(products)

    # Assert
    assert int(float(package.length)) == MIN_LENGTH
    assert int(float(package.width)) == MIN_WIDTH
    assert int(float(package.height)) == MIN_HEIGHT


def test_calculate_package_with_maximum_dimensions():
    """Must enforce maximum package dimensions."""
    # Arrange
    product = ProductInDBFactory(weight=5000, length=200, width=200, height=200, diameter=0)
    products = [product]

    # Act
    package = calculate_package(products)

    # Assert
    assert int(float(package.length)) == MAX_LENGTH
    assert int(float(package.width)) == MAX_WIDTH
    assert int(float(package.height)) == MAX_HEIGHT


def test_calculate_package_with_diameter_when_no_width():
    """Must use diameter when width is zero."""
    # Arrange
    product = ProductInDBFactory(weight=800, length=20, width=0, height=10, diameter=15)
    products = [product]

    # Act
    package = calculate_package(products)

    # Assert
    assert isinstance(package, FreightPackage)
    assert package.weight == "800"


def test_calculate_package_raises_metric_error_when_no_dimensions():
    """Must raise MetricError when product has no width or diameter."""
    # Arrange
    product = ProductInDBFactory(weight=500, length=20, width=0, height=10, diameter=0)
    products = [product]

    # Act / Assert
    with pytest.raises(MetricError):
        calculate_package(products)
