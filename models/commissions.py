from sqlalchemy import Boolean, Column, DateTime, Integer

from app.infra.database import Base


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
