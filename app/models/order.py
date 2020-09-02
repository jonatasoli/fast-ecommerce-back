from sqlalchemy.orm import backref, relationship
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
from sqlalchemy.types import JSON
from sqlalchemy.dialects.postgresql import ARRAY
from passlib.hash import pbkdf2_sha512

from constants import DocumentType
from ext.database import Base


class Product(Base):
    id = Column(Integer, nullable=False, primary_key=True)
    name = Column(String)
    uri = Column(String)
    price = Column(Integer)
    direct_sales = Column(Boolean, default=False)
    upsell = Column(ARRAY(Integer), nullable=True)
    description = Column(String)
    image_path = Column(String)
    installments_config = Column(Integer, nullable=True)
    installments_list = Column(ARRAY(JSON), nullable=True)


class Invoice(Base):
    id = Column(Integer, nullable=False, primary_key=True)
    customer_id = Column(Integer, ForeignKey("user.id"))
    customer = relationship("User", backref=backref("invoice", uselist=False), foreign_keys=[customer_id])
    invoice_date = Column(DateTime)
    invoice_items_id = Column(Integer)


class InvoiceItems(Base):
    id = Column(Integer, nullable=False, primary_key=True)
    invoice_id = Column(Integer, ForeignKey("invoice.id"))
    invoice = relationship("Invoice", backref=backref("invoice_items", uselist=False), foreign_keys=[invoice_id])
    product_id = Column(Integer, ForeignKey("product.id"))
    product = relationship("Product", backref=backref("product", uselist=False), foreign_keys=[product_id])
    quantity = Column(Integer)

