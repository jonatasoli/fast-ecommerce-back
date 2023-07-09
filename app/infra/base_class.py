from typing import Any, TypeVar
from sqlalchemy.ext.declarative import as_declarative, declared_attr


CLS = TypeVar('CLS')


@as_declarative()
class Base:
    id: Any   # noqa: A003
    __name__: str   # noqa: A003
    # Generate __tablename__ automatically
    @declared_attr
    def __tablename__(cls: CLS) -> str:   # noqa: N805
        """Generate __tablename__ automatically."""
        return cls.__name__.lower()
