"""Tests for base_class module."""
import pytest
from sqlalchemy import Column, Integer

from app.infra.base_class import Base


def test_base_class_tablename():
    """Test Base class generates __tablename__ automatically."""
    # Setup
    class UserModel(Base):
        """User model for testing."""

        id = Column(Integer, primary_key=True)

    # Act
    tablename = UserModel.__tablename__

    # Assert
    assert tablename == 'usermodel'


def test_base_class_inheritance():
    """Test Base class can be inherited."""
    # Setup
    class ProductModel(Base):
        """Product model for testing."""

        id = Column(Integer, primary_key=True)

    # Act
    instance = ProductModel()

    # Assert
    assert isinstance(instance, Base)
    assert hasattr(instance, '__tablename__')


def test_base_class_custom_tablename():
    """Test Base class respects custom __tablename__."""
    # Setup
    class CustomModel(Base):
        """Custom model with explicit tablename."""

        __tablename__ = 'custom_table'
        id = Column(Integer, primary_key=True)

    # Act
    tablename = CustomModel.__tablename__

    # Assert
    assert tablename == 'custom_table'

