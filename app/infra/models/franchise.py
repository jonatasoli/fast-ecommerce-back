from sqlalchemy import Boolean, Column, Integer, String

from app.infra.models.base import Base


class Franchise(Base):
    __tablename__ = "franchise"

    franchise_id = Column(Integer, nullable=False, primary_key=True)
    name = Column(String)
    active = Column(Boolean)
    communication_name = Column(String)
    description = Column(String)
    franshisee_name = Column(String)
    franshisee_id = Column(Integer)
