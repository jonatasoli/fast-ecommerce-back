from sqlalchemy.orm import Mapped, mapped_column

from app.infra.models.base import Base


class Role(Base):
    __tablename__ = 'role'

    role_id: Mapped[int] = mapped_column(primary_key=True)
    role: Mapped[str]
    active: Mapped[bool] = mapped_column(default=True)
