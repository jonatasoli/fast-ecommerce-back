from sqlalchemy.orm import backref, relationship
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
from passlib.hash import pbkdf2_sha512
from loguru import logger

from constants import DocumentType
from ext.database import Base


class CommissionsTransactions(Base):
    id = Column(Integer, nullable=False, primary_key=True)
    user_id = Column(Integer)
    transaction_id = Column(Integer)
    commissions = Column(Integer)
    date_created = Column(DateTime)
    released = Column(Boolean)
    paid = Column(Boolean)


class CommissionsWallet(Base):
    id = Column(Integer, nullable=False, primary_key=True)
    user_id = Column(Integer)
    commissions_total = Column(Integer)
    date_created = Column(DateTime)
    released = Column(Boolean)
    paid = Column(Boolean)
