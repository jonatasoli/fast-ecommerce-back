from pydantic import BaseModel, ConfigDict

from pydantic.dataclasses import dataclass
from sqlalchemy.orm import sessionmaker
from app.infra.database import get_async_session as get_session
from typing import Any
from app.catalog import uow as catalog_uow


class Command(BaseModel):
    """Command to use in the application."""

    db: sessionmaker
    catalog_uow: Any

    model_config = ConfigDict(arbitrary_types_allowed=True)


async def bootstrap(
    db: sessionmaker = get_session(),
    catalog_uow: Any = catalog_uow,
) -> Command:
    """Create a command function to use in the application."""
    return Command(
        db=db,
        catalog_uow=catalog_uow,
    )
