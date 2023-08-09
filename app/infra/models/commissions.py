from sqlalchemy import Boolean, Column, DateTime, Integer

from app.infra.models.base import Base


class CommissionsTransactions(Base):
    __tablename__ = 'commissions_transactions'

    commissions_transactions_id = Column(
        Integer,
        nullable=False,
        primary_key=True,
    )
    user_id = Column(Integer)
    transaction_id = Column(Integer)
    commissions = Column(Integer)
    date_created = Column(DateTime)
    released = Column(Boolean)
    paid = Column(Boolean)


class CommissionsWallet(Base):
    __tablename__ = 'commissions_wallet'

    commissions_wallet_id = Column(Integer, nullable=False, primary_key=True)
    user_id = Column(Integer)
    commissions_total = Column(Integer)
    date_created = Column(DateTime)
    released = Column(Boolean)
    paid = Column(Boolean)
