from constants import Roles
from ext.database import Base

from sqlalchemy import Column, Integer, String


class Role(Base):
    id = Column(Integer, nullable=False, primary_key=True)
    status = Column(String(20), default="deactivated")
    role = Column(String(64), default="USER")
