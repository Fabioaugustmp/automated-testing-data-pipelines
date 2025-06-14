# app/models/transaction.py
from sqlalchemy import Column, Integer, String, Float, DateTime
from app.db.base import Base

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, index=True)
    mcc = Column(String, index=True)  # Merchant Category Code
    valor = Column(Float)
    data = Column(DateTime)