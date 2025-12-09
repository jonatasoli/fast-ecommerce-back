from typing import Any, TypeVar, Self
from sqlalchemy.ext.declarative import as_declarative, declared_attr


CLS = TypeVar('CLS')


@as_declarative()
class Base:
    @declared_attr
    def __tablename__(cls) -> str:  # noqa: N805
        """Generate __tablename__ automatically."""
        return cls.__name__.lower()
