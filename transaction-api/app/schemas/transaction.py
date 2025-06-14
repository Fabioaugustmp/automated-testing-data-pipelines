# app/schemas/transaction.py
import datetime
from pydantic import BaseModel, Field

class TransactionBase(BaseModel):
    nome: str = Field(..., example="Restaurante Comida Boa")
    mcc: str = Field(..., example="5812")
    valor: float = Field(..., gt=0, example=99.90)

class TransactionCreate(TransactionBase):
    pass

class TransactionResponse(TransactionBase):
    id: int
    data: datetime.datetime

    class Config:
        orm_mode = True