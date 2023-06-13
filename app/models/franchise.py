from loguru import logger
from passlib.hash import pbkdf2_sha512
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import backref, relationship

from constants import DocumentType
from ext.database import Base


class User(Base):
    id = Column(Integer, nullable=False, primary_key=True)
    name = Column(String)
    active = Column(Boolean)
    communication_name = Column(String)
    description = Column(String)
    franshisee_name = Column(String)
    franshisee_id = Column(Integer)
